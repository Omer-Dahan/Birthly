import json
from pathlib import Path
from difflib import get_close_matches

_NAMES_DATA = None

def _load_names():
    global _NAMES_DATA
    if _NAMES_DATA is None:
        path = Path(__file__).parent / "names.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                _NAMES_DATA = {
                    "m": set(data.get("m", [])),
                    "f": set(data.get("f", [])),
                    "unisex": set(data.get("unisex", []))
                }
        else:
            _NAMES_DATA = {"m": set(), "f": set(), "unisex": set()}

def detect_gender(name: str) -> str | None:
    """
    מזהה אוטומטית אם השם הוא של גבר או אישה.
    מנקה את המחרוזת (לוקח מילה ראשונה) ובודק מול מאגר הלמ"ס.
    מחזיר "m", "f" או None (אם לא ידוע, או אם יוניסקס).
    """
    _load_names()
    
    parts = name.split()
    if not parts:
        return None
        
    # ניקוי: לוקחים את המילה הראשונה
    first_name = parts[0].strip()
    
    # חיפוש מדויק
    if first_name in _NAMES_DATA["unisex"]:
        return None
    if first_name in _NAMES_DATA["m"]:
        return "m"
    if first_name in _NAMES_DATA["f"]:
        return "f"
        
    # חיפוש מקורב למקרה של שגיאת כתיב (מאוד מחמיר - יחס של 0.85 לפחות)
    # difflib.get_close_matches uses SequenceMatcher
    all_m = list(_NAMES_DATA["m"])
    all_f = list(_NAMES_DATA["f"])
    
    # Since checking thousands of names with difflib is slow, we check only if length > 2
    # To optimize, we can filter names that have similar length first
    if len(first_name) > 2:
        m_matches = get_close_matches(first_name, all_m, n=1, cutoff=0.85)
        f_matches = get_close_matches(first_name, all_f, n=1, cutoff=0.85)
        
        if m_matches and not f_matches:
            return "m"
        if f_matches and not m_matches:
            return "f"
            
    return None
