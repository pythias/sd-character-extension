import cv2
import base64
import io
import numpy as np

from typing import Optional, List
from modules import scripts, processing

from character import lib, requests
from character.metrics import hDF

REPAIRER_NAME = "face editor ex"
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
        face_margin: float = 1.6,
        confidence: float = 0.97,
        strength1: float = 0.4,
        strength2: float = 0.0,
        max_face_count: int = 20,
        mask_size: int = 24,
        mask_blur: int = 0,
        prompt_for_face: str = '',
        apply_inside_mask_only: bool = False,
        save_original_image: bool = False,
        show_intermediate_steps: bool = False,
        apply_scripts_to_faces: bool = False,
        **_kwargs,
    ):
        self.enabled = enabled
        self.face_margin = face_margin
        self.confidence = confidence
        self.strength1 = strength1
        self.strength2 = strength2
        self.max_face_count = max_face_count
        self.mask_size = mask_size
        self.mask_blur = mask_blur
        self.prompt_for_face = prompt_for_face
        self.apply_inside_mask_only = apply_inside_mask_only
        self.save_original_image = save_original_image
        self.show_intermediate_steps = show_intermediate_steps
        self.apply_scripts_to_faces = apply_scripts_to_faces

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
    return script.title().lower() == REPAIRER_NAME


def require_face(request):
    # 老版本，所以在基础request里
    return requests.get_extra_value(request, "crop_face", False)


def require_face_repairer(request):
    return requests.get_extra_value(request, "repair_face", True)


def keep_original_image(request):
    return requests.get_extra_value(request, "keep_original", False)


def apply_face_repairer(p):
    if not require_face_repairer(p):
        return

    values = requests.get_extra_value(p, 'face_repair_params', {})
    values["enabled"] = True
    lib.log(f"ENABLE-FACE-REPAIRER, {values}")

    unit = FaceUnit(**values)

    requests.update_script_args(p, REPAIRER_NAME, [vars(unit)])
    # request.alwayson_scripts.update({REPAIRER_NAME: {'args': [vars(unit)]}})
