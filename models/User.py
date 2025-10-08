from typing import Any, Dict, List


class User(object):
    def __init__(self, tweet_json: Dict[str, Any]):
        user_json = tweet_json.get('user', {})
        self.id = user_json.get('id', None)
        self.screen_name = user_json.get('screen_name', None)
        self.name = user_json.get('name', None)
        self.description = user_json.get('description', None)
        self.verified = user_json.get('verified', False)
        self.protected = user_json.get('protected', False)
        self.followers_count = user_json.get('followers_count', None)
        self.friends_count = user_json.get('friends_count', None)
        self.statuses_count = user_json.get('statuses_count', None)
        self.created_at = user_json.get('created_at', None)
        self.location = user_json.get('location', None)
        self.url = user_json.get('url', None)

    def get_dict_representation(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'screen_name': self.screen_name,
            'name': self.name,
            'description': self.description,
            'verified': self.verified,
            'protected': self.verified,
            'followers_count': self.followers_count,
            'friends_count': self.friends_count,
            'statuses_count': self.statuses_count,
            'created_at': self.created_at,
            'location': self.location,
            'url': self.url,
        }

    @staticmethod
    def get_field_names() -> List[str]:
        return [
            'id',
            'screen_name',
            'name',
            'description',
            'verified',
            'protected',
            'followers_count',
            'friends_count',
            'statuses_count',
            'created_at',
            'location',
            'url',
        ]

    @staticmethod
    def get_table_name() -> str:
        return 'users'

    @staticmethod
    def get_conflict_columns() -> List[str]:
        return ['id']