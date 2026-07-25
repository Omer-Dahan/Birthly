import hebrew_names
import json

hebrew_names.load_cumulatives()
m = set([n for n, c in hebrew_names.CUMULATIVES['jew']['male']['first']])
f = set([n for n, c in hebrew_names.CUMULATIVES['jew']['female']['first']])

with open('names_gender.json', 'w', encoding='utf-8') as out:
    json.dump({'m': list(m), 'f': list(f)}, out, ensure_ascii=False)
