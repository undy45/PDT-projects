from typing import Any, Dict, List

import Util


class TweetUrl(object):
    def __init__(self, tweet_url_json: Dict[str, Any], tweet_id: int):
        self.tweet_id = tweet_id
        
        self.url = Util.format_field(tweet_url_json, 'url')
        self.expanded_url = Util.format_field(tweet_url_json, 'expanded_url')
        self.display_url = Util.format_field(tweet_url_json, 'display_url')
        self.unwound_url = Util.format_field(tweet_url_json, 'unwound_url')

    def get_dict_representation(self) -> Dict[str, Any]:
        return {
            'tweet_id': self.tweet_id,
            'url': self.url,
            'expanded_url': self.expanded_url,
            'display_url': self.display_url,
            'unwound_url': self.unwound_url,
        }

    @staticmethod
    def get_field_names() -> List[str]:
        return [
            'tweet_id',
            'url',
            'expanded_url',
            'display_url',
            'unwound_url',
        ]

    @staticmethod
    def get_table_name() -> str:
        return 'tweet_urls'

    @staticmethod
    def get_conflict_columns() -> List[str]:
        return []