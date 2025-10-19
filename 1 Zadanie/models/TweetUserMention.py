from typing import Any, Dict, List

import Util


class TweetUserMention(object):
    def __init__(self, tweet_user_mention_json: Dict[str, Any], tweet_id: int):
        self.tweet_id = tweet_id
        self.mentioned_user_id = tweet_user_mention_json.get('user_id', None)
        self.mentioned_screen_name = Util.format_field(tweet_user_mention_json, 'screen_name')
        self.mentioned_name = Util.format_field(tweet_user_mention_json, 'name')

    def get_dict_representation(self) -> Dict[str, Any]:
        return {
            'tweet_id': self.tweet_id,
            'mentioned_user_id': self.mentioned_user_id,
            'mentioned_screen_name': self.mentioned_screen_name,
            'mentioned_name': self.mentioned_name,
        }

    @staticmethod
    def get_field_names() -> List[str]:
        return [
            'tweet_id',
            'mentioned_user_id',
            'mentioned_screen_name',
            'mentioned_name',
        ]

    @staticmethod
    def get_table_name() -> str:
        return 'tweet_user_mentions'

    @staticmethod
    def get_conflict_columns() -> List[str]:
        return []
