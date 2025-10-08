from typing import Any, Dict, List


class Place(object):
    def __init__(self, tweet_json: Dict[str, Any]):
        place_json = tweet_json.get('place', {})
        self.id = place_json.get('id', None)
        self.full_name = place_json.get('full_name', None)
        self.country = place_json.get('country', None)
        self.country_code = place_json.get('country_code', None)
        self.place_type = place_json.get('place_type', None)

    def get_dict_representation(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'full_name': self.full_name,
            'country': self.country,
            'country_code': self.country_code,
            'place_type': self.place_type,
        }

    @staticmethod
    def get_field_names() -> List[str]:
        return [
            'id',
            'full_name',
            'country',
            'country_code',
            'place_type',
        ]

    @staticmethod
    def get_table_name() -> str:
        return 'places'

    @staticmethod
    def get_conflict_columns() -> List[str]:
        return ['id']