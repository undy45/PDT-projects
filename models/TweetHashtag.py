from typing import List, Dict, Any


class TweetHashtag(object):
    def __init__(self, tweet_id: int, hashtag_id: int):
        self.hashtag_id = hashtag_id
        self.tweet_id = tweet_id

    def get_dict_representation(self) -> Dict[str, Any]:
        return {
            'tweet_id': self.tweet_id,
            'hashtag_id': self.hashtag_id,
        }

    @staticmethod
    def get_field_names() -> List[str]:
        return [
            'tweet_id',
            'hashtag_id',
        ]

    @staticmethod
    def get_table_name() -> str:
        return 'tweet_hashtag'

    @staticmethod
    def get_conflict_columns() -> List[str]:
        return TweetHashtag.get_field_names()