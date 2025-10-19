DROP TABLE IF EXISTS tweet_hashtag;
DROP TABLE IF EXISTS tweet_media;
DROP TABLE IF EXISTS tweet_user_mentions;
DROP TABLE IF EXISTS tweet_urls;
DROP TABLE IF EXISTS hashtags;
DROP TABLE IF EXISTS tweets;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS places;

CREATE TABLE users (
    id BIGINT PRIMARY KEY,
    screen_name TEXT,
    name TEXT,
    description TEXT,
    verified BOOLEAN,
    protected BOOLEAN,
    followers_count INTEGER,
    friends_count INTEGER,
    statuses_count INTEGER,
    created_at TIMESTAMP,
    location TEXT,
    url TEXT
);

CREATE TABLE places (
    id TEXT PRIMARY KEY,
    full_name TEXT,
    country TEXT,
    country_code TEXT,
    place_type TEXT
);

CREATE TABLE tweets (
    id BIGINT PRIMARY KEY,
    created_at TIMESTAMP,
    full_text TEXT,
    display_from INTEGER,
    display_to INTEGER,
    lang TEXT,
    user_id BIGINT NULL REFERENCES users(id) ON DELETE SET NULL,
    source TEXT,
    in_reply_to_status_id BIGINT,
    quoted_status_id BIGINT,
    retweeted_status_id BIGINT,
    place_id TEXT REFERENCES places(id) ON DELETE SET NULL,
    retweet_count INTEGER,
    favorite_count INTEGER,
    possibly_sensitive BOOLEAN
);

CREATE TABLE hashtags (
    id BIGSERIAL PRIMARY KEY,
    tag TEXT UNIQUE
);

CREATE TABLE tweet_hashtag (
    tweet_id BIGINT REFERENCES tweets(id) ON DELETE CASCADE,
    hashtag_id BIGINT REFERENCES hashtags(id) ON DELETE CASCADE,
    PRIMARY KEY (tweet_id, hashtag_id)
);

CREATE TABLE tweet_urls (
    tweet_id BIGINT REFERENCES tweets(id) ON DELETE CASCADE,
    url TEXT,
    expanded_url TEXT,
    display_url TEXT,
    unwound_url TEXT
);

CREATE TABLE tweet_user_mentions (
    tweet_id BIGINT REFERENCES tweets(id) ON DELETE CASCADE,
    mentioned_user_id BIGINT,
    mentioned_screen_name TEXT,
    mentioned_name TEXT
);

CREATE TABLE tweet_media (
    tweet_id BIGINT REFERENCES tweets(id) ON DELETE CASCADE,
    media_id BIGINT PRIMARY KEY,
    type TEXT,
    media_url TEXT,
    media_url_https TEXT,
    display_url TEXT,
    expanded_url TEXT
);

CREATE INDEX idx_users_screen_name ON users(screen_name);

CREATE INDEX idx_tweets_user_id ON tweets(user_id);
CREATE INDEX idx_tweets_in_reply_to_status_id ON tweets(in_reply_to_status_id);
CREATE INDEX idx_tweets_quoted_status_id ON tweets(quoted_status_id);
CREATE INDEX idx_tweets_retweeted_status_id ON tweets(retweeted_status_id);
CREATE INDEX idx_tweets_place_id ON tweets(place_id);

CREATE INDEX idx_hashtags_tag ON hashtags(tag);

CREATE INDEX idx_tweet_hashtag_tweet_id ON tweet_hashtag(tweet_id);
CREATE INDEX idx_tweet_hashtag_hashtag_id ON tweet_hashtag(hashtag_id);

CREATE INDEX idx_tweet_urls_tweet_id ON tweet_urls(tweet_id);

CREATE INDEX idx_tweet_user_mentions_tweet_id ON tweet_user_mentions(tweet_id);
CREATE INDEX idx_tweet_user_mentions_mentioned_user_id ON tweet_user_mentions(mentioned_user_id);

CREATE INDEX idx_tweet_media_tweet_id ON tweet_media(tweet_id);

