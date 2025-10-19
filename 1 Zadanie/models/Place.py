from typing import Any, Dict, List

import Util


class Place(object):
    def __init__(self, tweet_json: Dict[str, Any]):
        place_json = tweet_json.get('place', {})
        self.id = Util.format_field(place_json, 'id')
        self.full_name = Util.format_field(place_json, 'full_name')
        self.country = Util.format_field(place_json, 'country')
        self.country_code = Util.format_field(place_json, 'country_code')
        self.place_type = Util.format_field(place_json, 'place_type')

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