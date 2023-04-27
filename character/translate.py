from character.lib import models_path, log, LogLevel
from transformers import MBart50TokenizerFast, MBartForConditionalGeneration

model_name = "facebook/mbart-large-50-many-to-many-mmt"
src_lang = "zh_CN"
tgt_lang = "en_XX"

class PromptTranslator:
    def __init__(self):
        self.model = MBartForConditionalGeneration.from_pretrained(model_name, cache_dir=models_path)
        self.tokenizer = MBart50TokenizerFast.from_pretrained(model_name, src_lang=src_lang, tgt_lang=tgt_lang, cache_dir=models_path)

        log(message=f"Translator loaded, model: {model_name}")

    def translate(self, text: str) -> str:
        encoded_input = self.tokenizer(text, return_tensors="pt")
        generated_tokens = self.model.generate(
            **encoded_input, forced_bos_token_id=self.tokenizer.lang_code_to_id[tgt_lang]
        )
        translated_text = self.tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)
        return translated_text[0]

translator = PromptTranslator()
