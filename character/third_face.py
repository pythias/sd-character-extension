import cv2
import base64
import io
import numpy as np
import os
import sys

from typing import Optional, List
from modules import scripts, processing

from character import lib, requests
from character.metrics import hDF

# from modules.paths_internal import extensions_dir
# sys.path.append(os.path.join(extensions_dir, "sd-face-editor"))

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


def require_face(request):
    # 老版本，所以在基础request里
    return requests.get_extra_value(request, "crop_face", False)


def require_face_repairer(request):
    # return False
    return requests.get_extra_value(request, "repair_face", True)


def keep_original_image(request):
    return requests.get_extra_value(request, "keep_original", False)


def apply_face_repairer(p):
    if not require_face_repairer(p):
        return
    
    values = requests.get_extra_value(p, 'face_repair_params', {})
    values["enabled"] = True
    if "prompt_for_face" not in values:
        values["prompt_for_face"] = "beauty"

    requests.update_script_args(p, REPAIRER_NAME, [values])

    lib.log(f"ENABLE-FACE-REPAIRER, {values}")
