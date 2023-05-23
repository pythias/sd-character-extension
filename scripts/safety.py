import gradio as gr
import time

from character import lib, face
from character.lib import log, get_or_default
from character.nsfw import image_has_nsfw, image_has_illegal_words
from character.metrics import cNSFW, cIllegal

from modules import shared, scripts
from modules.processing import Processed, StableDiffusionProcessing

class Script(scripts.Script):
    def title(self):
        return "Character Safety"

    def show(self, is_img2img):
        return False

    def ui(self, is_img2img):
        return [gr.Checkbox(label="Character On UI", value=True)]
        
    def postprocess(self, p: StableDiffusionProcessing, processed: Processed, *args):
        # todo 和脸部修复的最后一个script操作冲突
        return

log("Safety loaded")