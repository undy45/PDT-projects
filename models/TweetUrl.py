from typing import Any, Dict, List


class TweetUrl(object):
    def __init__(self, tweet_url_json: Dict[str, Any], tweet_id: int):
        self.tweet_id = tweet_id
        self.url = tweet_url_json.get('url', None)
        self.expanded_url = tweet_url_json.get('expanded_url', None)
        self.display_url = tweet_url_json.get('display_url', None)
        self.unwound_url = tweet_url_json.get('unwound_url', None)

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