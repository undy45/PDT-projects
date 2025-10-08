import gzip
import json
import io
import csv
import os
from typing import Dict, Any, Tuple, List

import psycopg2
from tqdm import tqdm

from models.Hashtag import Hashtag
from models.Place import Place
from models.Tweet import Tweet
from models.TweetHashtag import TweetHashtag
from models.TweetMedia import TweetMedia
from models.TweetUrl import TweetUrl
from models.TweetUserMention import TweetUserMention
from models.User import User

# Configurations
FILE_LIST = [f for f in os.listdir('importy') if os.path.isfile(os.path.join('importy', f))]
BATCH_SIZE = 10**7

PG_CONN_INFO = "dbname=twitter user=postgres password=FMAis#1anime host=localhost"

OBJECTS: List[Any] = [
    Hashtag,
    Place,
    User,
    Tweet,
    TweetHashtag,
    TweetMedia,
    TweetUrl,
    TweetUserMention
]


def parse_json(tweet_json: Dict[str, Any], last_hashtag_id: int) -> Tuple[
    Tweet, User, Place, List[TweetMedia], List[TweetUrl], List[TweetUserMention], List[TweetHashtag], List[Hashtag]]:
    tweet = Tweet(tweet_json)
    user = User(tweet_json) if tweet_json.get('user', None) else None
    place = Place(tweet_json) if tweet_json.get('place', None) else None
    entities_key = 'extended_entities' if tweet_json.get('truncated', False) else 'entities'
    entities = tweet_json.get(entities_key, {})
    medias = list(map(lambda m: TweetMedia(m, tweet.id), entities.get('media', [])))
    urls = list(map(lambda u: TweetUrl(u, tweet.id), entities.get('urls', [])))
    user_mentions = list(map(lambda m: TweetUserMention(m, tweet.id), entities.get('user_mentions', [])))
    hashtags = []
    tweet_hashtags = []
    for i, hashtag_json in enumerate(entities.get('hashtags', [])):
        hashtag_id = last_hashtag_id + i + 1
        hashtags.append(Hashtag(hashtag_json, hashtag_id))
        tweet_hashtags.append(TweetHashtag(tweet.id, hashtag_id))
    return tweet, user, place, medias, urls, user_mentions, tweet_hashtags, hashtags


def dicts_to_csv_stringio(fieldnames, rows):
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    output.seek(0)
    return output


def copy_to_temp_and_insert(conn, row_object, csv_buffer):
    with conn.cursor() as cur:
        temp_table_name = 'tmp_' + row_object.get_table_name()
        cur.execute(
            f"CREATE TEMP TABLE IF NOT EXISTS {temp_table_name} (LIKE {row_object.get_table_name()} INCLUDING DEFAULTS) ON COMMIT DROP;")

        cur.copy_expert(f"COPY {temp_table_name} ({', '.join(row_object.get_field_names())}) FROM STDIN CSV HEADER", csv_buffer)

        pk_cols = ', '.join(row_object.get_conflict_columns())
        if row_object.get_conflict_columns():
            cur.execute(f"""
                        INSERT INTO {row_object.get_table_name()} ({', '.join(row_object.get_field_names())})
                        SELECT {', '.join(row_object.get_field_names())} FROM {temp_table_name}
                        ON CONFLICT ({pk_cols}) DO NOTHING;
                    """)
        else:
            cur.execute(f"""
                        INSERT INTO {row_object.get_table_name()} ({', '.join(row_object.get_field_names())})
                        SELECT {', '.join(row_object.get_field_names())} FROM {temp_table_name};
                    """)
    conn.commit()


def getDbHashtags(hashtags: List[Dict[str, Any]], conn) -> List[Dict[str, Any]]:
    with conn.cursor() as cur:
        tags = ['\'' + h['tag'] + '\'' for h in hashtags]
        tags = ', '.join(tags)
        cur.execute(f"SELECT id, tag FROM {Hashtag.get_table_name()} WHERE tag in ({tags});")
        existing = cur.fetchall()
        return [{'id': id, 'tag': tag} for id, tag in existing]



def make_hashtags_unique(rows: Dict[Any, List[Dict[str, Any]]],
                         conn) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    hashtags = rows[Hashtag]
    tweet_hashtags = rows[TweetHashtag]
    reverse_index_hashtags: Dict[str, int] = {}
    duplicate_hashtags_index: List[int] = []
    reverse_index_tweet_hashtags: Dict[int, List[int]] = {}
    for i, tweet_hashtag in tqdm(enumerate(tweet_hashtags), desc=f"Creating reverse_index_tweet_hashtags", position=1):
        key = tweet_hashtag['hashtag_id']
        reverse_index_tweet_hashtags[key] = reverse_index_tweet_hashtags.get(key, []) + [i]

    for i, hashtag in tqdm(enumerate(hashtags), desc=f"Removing duplicates locally", total=len(hashtags), position=1):
        tag_text = hashtag['tag']
        if tag_text not in reverse_index_hashtags:
            reverse_index_hashtags[tag_text] = hashtag['id']
            continue

        duplicate_hashtags_index.append(i)
        tweet_hashtag_indices = reverse_index_tweet_hashtags.pop(hashtag['id'])
        new_id = reverse_index_hashtags[tag_text]
        for j in tweet_hashtag_indices:
            tweet_hashtags[j]['hashtag_id'] = new_id
        reverse_index_tweet_hashtags[new_id] = reverse_index_tweet_hashtags.get(new_id, []) + tweet_hashtag_indices

    for i in range(len(duplicate_hashtags_index) - 1, -1, -1):
        hashtags.pop(duplicate_hashtags_index[i])

    duplicate_hashtags = getDbHashtags(hashtags, conn)
    for hashtag in tqdm(duplicate_hashtags, desc=f"Removing duplicates with DB", total=len(duplicate_hashtags), position=1):
        tag_text = hashtag['tag']
        hashtag_id_to_delete = reverse_index_hashtags[tag_text]
        tweet_hashtag_indices = reverse_index_tweet_hashtags.pop(hashtag_id_to_delete)
        for i in tweet_hashtag_indices:
            tweet_hashtags[i]['hashtag_id'] = hashtag['id']
        reverse_index_hashtags[tag_text] = hashtag['id']
    return tweet_hashtags, hashtags


def count_lines_gz(file_path):
    with gzip.open(file_path, 'rt', encoding='utf-8') as f:
        return sum(1 for _ in f)


def process_file(conn, file_path):
    rows = {
        Tweet: [],
        Hashtag: [],
        Place: [],
        TweetHashtag: [],
        TweetMedia: [],
        TweetUrl: [],
        TweetUserMention: [],
        User: [],
    }
    total_tweets = 0
    total_users = 0
    last_used_hashtag_id = 0

    total_lines = count_lines_gz(file_path)

    with gzip.open(file_path, 'rt', encoding='utf-8') as f:
        for line in tqdm(f, desc=f"Processing {file_path}", total=total_lines, position=1):
            tweet_json = json.loads(line)
            tweet, user, place, medias, urls, user_mentions, tweet_hashtags, hashtags = parse_json(tweet_json, last_used_hashtag_id)
            last_used_hashtag_id += len(hashtags)
            rows[Tweet].append(tweet.get_dict_representation())
            if user:
                rows[User].append(user.get_dict_representation())
            if place:
                rows[Place].append(place.get_dict_representation())
            rows[TweetMedia] += list(map(lambda m: m.get_dict_representation(), medias))
            rows[TweetUrl] += list(map(lambda m: m.get_dict_representation(), urls))
            rows[TweetUserMention] += list(map(lambda m: m.get_dict_representation(), user_mentions))
            rows[TweetHashtag] += list(map(lambda m: m.get_dict_representation(), tweet_hashtags))
            rows[Hashtag] += list(map(lambda m: m.get_dict_representation(), hashtags))

            # Flush batch if size reached
            if len(rows[Tweet]) < BATCH_SIZE:
                continue
            rows[TweetHashtag], rows[Hashtag] = make_hashtags_unique(rows, conn)
            for row_object in OBJECTS:
                if not rows[row_object]:
                    continue
                tmp_csv = dicts_to_csv_stringio(row_object.get_field_names(), rows[row_object])
                copy_to_temp_and_insert(conn, row_object, tmp_csv)
                rows[row_object].clear()

    # Flush remaining rows after loop
    rows[TweetHashtag], rows[Hashtag] = make_hashtags_unique(rows, conn)
    for row_object in OBJECTS:
        if not rows[row_object]:
            continue
        tmp_csv = dicts_to_csv_stringio(row_object.get_field_names(), rows[row_object])
        copy_to_temp_and_insert(conn, row_object, tmp_csv)
        rows[row_object].clear()
    print(f"Finished processing {file_path}: imported {total_tweets} tweets and {total_users} unique users")


def main():
    conn = psycopg2.connect(PG_CONN_INFO)
    try:
        for file_path in tqdm(FILE_LIST, total=len(FILE_LIST), desc="Processing files", position=0):
            process_file(conn, 'importy/' + file_path)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
