from character.lib import log
from character.translate import *

translator_preload_text = "翻译一下什么叫惊喜"
translator_translated_text = translator.translate(translator_preload_text)

log(message=f"{translator_preload_text}, translated: {translator_translated_text}")
