from typing import Any, Dict, List


class TweetMedia(object):
    def __init__(self, tweet_media_json: Dict[str, Any], tweet_id: int):
        self.tweet_id = tweet_id
        self.media_id = tweet_media_json.get('id')
        self.type = tweet_media_json.get('type', None)
        self.media_url = tweet_media_json.get('media_url', None)
        self.media_url_https = tweet_media_json.get('media_url_https', None)
        self.display_url = tweet_media_json.get('display_url', None)
        self.expanded_url = tweet_media_json.get('expanded_url', None)

    def get_dict_representation(self) -> Dict[str, Any]:
        return {
            'tweet_id': self.tweet_id,
            'media_id': self.media_id,
            'type': self.type,
            'media_url': self.media_url,
            'display_url': self.display_url,
            'expanded_url': self.expanded_url,
        }

    @staticmethod
    def get_field_names() -> List[str]:
        return [
            'tweet_id',
            'media_id',
            'type',
            'media_url',
            'display_url',
            'expanded_url',
        ]

    @staticmethod
    def get_table_name() -> str:
        return 'tweet_media'

    @staticmethod
    def get_conflict_columns() -> List[str]:
        return ['media_id']