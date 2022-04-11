import json


__texts_file = open("texts.json", "r")
__texts = json.load(__texts_file)


__current_localization = "en"
__fallback_localization = "en"

def set_localization(localization: str):
    global __current_localization
    __current_localization = localization

def t(text_key: str) -> str:
    entry = __texts.get(text_key)
    if not entry:
        raise 'Text not present'

    return entry.get(__current_localization, entry[__fallback_localization])
