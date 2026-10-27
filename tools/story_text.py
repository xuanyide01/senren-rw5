"""Translate verified SCN presentation escapes, without unicode_escape decoding."""
def normalize_dialogue(text):
    return (text or '').replace('\\n','\n').replace('\r\n','\n').replace('\r','\n').replace('\u00a0',' ').strip('\ufeff\u200b\n')
