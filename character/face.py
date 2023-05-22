import cv2
import base64
import io
import numpy as np

from typing import Optional, List
from modules import scripts, processing

from character.metrics import hDF
from character.lib import log

REPAIRER_NAME = "FaceRepairer"
CROPPER_NAME = "FaceCropper"


@hDF.time()
def crop(image_base64) -> list:
    # Decode the base64 image
    image_data = base64.b64decode(image_base64)
    image_buffer = io.BytesIO(image_data)
    image_array = np.frombuffer(image_buffer.getvalue(), dtype=np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    # Convert the image to grayscale
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Load the Haar Cascade classifier for detecting faces
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

    # Detect faces in the image
    faces = face_cascade.detectMultiScale(gray_image, scaleFactor=1.1, minNeighbors=5)

    # Iterate through the faces detected
    cropped_face_base64s = []
    for (x, y, w, h) in faces:
        # Calculate the padding for width and height
        padding_w = int(w * 0.1)
        padding_h = int(h * 0.1)

        # Calculate the new coordinates including padding
        x1 = max(0, x - padding_w)
        y1 = max(0, y - padding_h)
        x2 = min(image.shape[1], x + w + padding_w)
        y2 = min(image.shape[0], y + h + padding_h)

        # Crop the face from the image with padding
        cropped_face = image[y1:y2, x1:x2]

        # Encode the cropped face as a base64 string
        _, face_buffer = cv2.imencode('.png', cropped_face)
        cropped_face_base64 = base64.b64encode(face_buffer).decode('utf-8')
        cropped_face_base64s.append(cropped_face_base64)

    return cropped_face_base64s


class FaceUnit:
    def __init__(
        self,
        enabled: bool = False,
        keep_original: bool = False,
        face_margin: float = 1.6,
        confidence: float = 0.97,
        face_denoising_strength: float = 0.4,
        entire_denoising_strength: float = 0.0,
        max_face_count: int = 20,
        mask_size: int = 24,
        mask_blur: int = 0,
        prompt_for_face: str = '',
        **_kwargs,
    ):
        self.enabled = enabled
        self.face_margin = face_margin
        self.confidence = confidence
        self.face_denoising_strength = face_denoising_strength
        self.entire_denoising_strength = entire_denoising_strength
        self.max_face_count = max_face_count
        self.mask_size = mask_size
        self.mask_blur = mask_blur
        self.prompt_for_face = prompt_for_face
        self.keep_original = keep_original

    def __eq__(self, other):
        if not isinstance(other, FaceUnit):
            return False

        return vars(self) == vars(other)


def get_unit(p: processing.StableDiffusionProcessing) -> Optional[FaceUnit]:
    script_runner = p.scripts
    script_args = p.script_args

    fr_script = find_face_repairer_script(script_runner)
    if fr_script is None:
        return None

    fr_script_args = script_args[fr_script.args_from:fr_script.args_to]
    if len(fr_script_args) == 0:
        return None

    if isinstance(fr_script_args[0], FaceUnit):
        return fr_script_args[0]

    return FaceUnit(*fr_script_args)


def find_face_repairer_script(script_runner: scripts.ScriptRunner) -> Optional[scripts.Script]:
    if script_runner is None:
        return None

    for script in script_runner.alwayson_scripts:
        if is_face_repairer_script(script):
            return script

    return None


def is_face_repairer_script(script: scripts.Script) -> bool:
    return script.title() == REPAIRER_NAME


def apply_face_repairer(request):
    if not getattr(request, "character_face_repair", False):
        return

    params = vars(request)
    keys = list(params.keys())
    values = {}
    for key in keys:
        if not key.startswith("character_face_repair_"):
            continue

        key = key[len("character_face_repair_"):]
        values[key] = params["character_face_repair_" + key]

    values["enabled"] = True
    unit = FaceUnit(**values)
    request.alwayson_scripts.update({REPAIRER_NAME: {'args': [unit]}})
