import cv2
import gradio as gr

from character import face, lib
from character.lib import log, get_or_default

import modules.scripts as scripts
from modules import shared, scripts
from modules.processing import Processed

class FaceCropper(scripts.Script):
    def __init__(self) -> None:
        super().__init__()

    def title(self):
        return face.CROPPER_NAME

    def show(self, is_img2img):
        return False

    def ui(self, is_img2img):
        enabled = gr.Checkbox(label="Enabled Face Detect", value=False)
        return [enabled]

    def postprocess(self, p, processed: Processed, enabled: bool, *args):
        # todo 脸部检测
        return

lib.log("Face loaded")
