from typing import Any, Dict, List

import Util


class Tweet(object):
    def __init__(self, tweet_json: Dict[str, Any]):
        self.id = tweet_json.get("id")
        self.created_at = tweet_json.get('created_at', None)
        if tweet_json.get('truncated', False):
            self.full_text = Util.format_field(tweet_json, ['extended_tweet', 'full_text'])
        else:
            self.full_text = Util.format_field(tweet_json, ['full_text'])
        display_text_range = tweet_json.get('display_text_range', [None, None])
        self.display_from = display_text_range[0]
        self.display_to = display_text_range[1]
        self.lang = Util.format_field(tweet_json, 'lang')
        self.user_id = (tweet_json.get('user', {}) or {}).get('id', None)
        self.source = Util.format_field(tweet_json, 'source')
        self.in_reply_to_status_id = tweet_json.get('in_reply_to_status_id', None)
        self.quoted_status_id = tweet_json.get('quoted_status_id', None)
        self.retweeted_status_id = (tweet_json.get('retweeted_status', {}) or {}).get('id', None)
        self.place_id = (tweet_json.get('place', {}) or {}).get('id', None)
        self.retweet_count = tweet_json.get('retweet_count', None)
        self.favorite_count = tweet_json.get('favorite_count', None)
        self.possibly_sensitive = tweet_json.get('possibly_sensitive', False)

    def get_dict_representation(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'created_at': self.created_at,
            'full_text': self.full_text,
            'display_from': self.display_from,
            'display_to': self.display_to,
            'lang': self.lang,
            'user_id': self.user_id,
            'source': self.source,
            'in_reply_to_status_id': self.in_reply_to_status_id,
            'quoted_status_id': self.quoted_status_id,
            'retweeted_status_id': self.retweeted_status_id,
            'place_id': self.place_id,
            'retweet_count': self.retweet_count,
            'favorite_count': self.favorite_count,
            'possibly_sensitive': self.possibly_sensitive,
        }

    @staticmethod
    def get_field_names() -> List[str]:
        return [
            'id',
            'created_at',
            'full_text',
            'display_from',
            'display_to',
            'lang',
            'user_id',
            'source',
            'in_reply_to_status_id',
            'quoted_status_id',
            'retweeted_status_id',
            'place_id',
            'retweet_count',
            'favorite_count',
            'possibly_sensitive',
        ]

    @staticmethod
    def get_table_name() -> str:
        return 'tweets'

    @staticmethod
    def get_conflict_columns() -> List[str]:
        return ['id']