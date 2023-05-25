import base64
import os
import uuid
import time
from io import BytesIO

from character import lib

from modules import shared


def required_save(request):
    response_format = lib.get_extra_value(request, "response_format", 'b64')
    return response_format == 'url'


def save_image(b64):
    """
    save base64 image to disk, return url
    """
    try:
        if b64.startswith("data:image/"):
            b64 = b64.split(";")[1].split(",")[1]
        img_bytes = base64.b64decode(b64)

        imd_relative_path = os.path.join("outputs", shared.cmd_opts.character_short_name, time.strftime("%Y%m%d"))
        img_dir = os.path.join(shared.cmd_opts.character_output_dir, imd_relative_path)
        if not os.path.exists(img_dir):
            os.makedirs(img_dir)

        img_filename = str(uuid.uuid4()) + '.png'
        img_filepath = os.path.join(img_dir, img_filename)
        with open(img_filepath, 'wb') as f:
            f.write(img_bytes)
        
        return os.path.join(shared.cmd_opts.character_host, imd_relative_path, img_filename)
    except Exception as e:
        lib.log("save_image error: %s" % e)
        return b64