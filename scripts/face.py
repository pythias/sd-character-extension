import cv2
import gradio as gr
import modules.scripts as scripts

from character import face, lib


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


lib.log("Face loaded")
