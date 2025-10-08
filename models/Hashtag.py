from typing import Any, Dict, List


class Hashtag(object):
    def __init__(self, hashtag_json: Dict[str, Any], db_id: int):
        self.id = db_id
        self.tag = hashtag_json.get('text', None)

    def get_dict_representation(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'tag': self.tag,
        }

    @staticmethod
    def get_field_names() -> List[str]:
        return [
            'id',
            'tag',
        ]

    @staticmethod
    def get_table_name() -> str:
        return 'hashtags'

    @staticmethod
    def get_conflict_columns() -> List[str]:
        return [
            'tag',
        ]