from typing import Any, Dict, List, Optional

def format_field(json: Dict[str, Any], path: List[str] | str) -> Optional[str]:
    if type(path) == str:
        path = [path]
    result: Any = json
    for p in path:
        if result is None:
            return None
        result = result.get(p, None)
    if result is None:
        return None
    return result.replace('\x00', '')