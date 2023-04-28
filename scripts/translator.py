from character.lib import log
from character.translate import translate 

translator_preload_text = "翻译一下什么叫惊喜"

log("Loading translator...")
log(message=f"{translator_preload_text}, translated: {translate(translator_preload_text)}")
