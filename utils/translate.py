from googletrans import Translator
import json

translator = Translator()
available_languages = ('ru', 'ja', 'zh-CN')

def isEmoji(word):
    try:
        return word[0] == ':' and word[-1] == ':'
    except:
        return False

def translate(locale, text):
    if locale == 'en':
        return text
    with open('./assets/translations/lang_%s.json' % locale, 'r', encoding='utf8', errors='ignore') as f:
        data = json.load(f)
    if text in data:
        return data[text]
    raw_trans = translator.translate(text, dest=locale, src='en')
    emojis = []
    for word in text.replace('\n', ' ').replace('\t', ' ').replace('\r', ' ').replace('.', ' ').replace('!', ' ').replace('?', ' ').replace(',', ' ').split(' '):
        if isEmoji(word):
            emojis.append(word)
            text = text.replace(word, '_E_M_O_J_I_')
    translated = translator.translate(text, dest=locale, src='en')
    if len(emojis) == 0:
        return translated.text
    try:
        return translated.text.replace('_E_M_O_J_I_', '%s') % tuple(emojis)
    except:
        return raw_trans.text
    