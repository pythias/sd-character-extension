import os
import sys

from character import lib, requests, names
from modules.paths_internal import extensions_dir
sys.path.append(os.path.join(extensions_dir, "sd-webui-controlnet"))
from scripts import external_code, global_state, controlnet_version

default_control_net_model = "lineart"
default_control_net_module = "lineart_realistic"
default_open_pose_model = "openpose"
default_open_pose_module = "openpose"
default_tile_model = "tile"
default_tile_module = "tile_resample"

control_net_models = external_code.get_models(update=True)
control_net_version = controlnet_version.version_flag

def _find_closest_cn_model_name(search: str):
    if not search:
        return None

    if search in global_state.cn_models:
        return search

    search = search.lower()
    if search in global_state.cn_models_names:
        return global_state.cn_models_names.get(search)
    
    applicable = [name for name in global_state.cn_models_names.keys() if search in name.lower()]
    if not applicable:
        return None

    applicable = sorted(applicable, key=lambda name: len(name))
    return global_state.cn_models_names[applicable[0]]

lib.log(f"ControlNet Loaded, version: {control_net_version}, {_find_closest_cn_model_name('lineart')}, {_find_closest_cn_model_name('openpose')}, {_find_closest_cn_model_name('tile')}")

def apply_args(request):
    units = []
    units.append(_get_cn_image_unit(request, 0, default_control_net_module, default_control_net_model))
    units.append(_get_cn_image_unit(request, 1))
    units.append(_get_cn_image_unit(request, 2))
    units.append(_get_cn_image_unit(request, 3))
    units.append(_get_cn_image_unit(request, 4))

    requests.update_script_args(request, "ControlNet", [_to_process_unit(unit) for unit in units])

def _get_cn_image_unit(request, i, default_module = "", default_model = ""):
    unit = _get_cn_empty_unit()
    image_b64 = requests.get_extra_value(request, f"image_cn_{i}", default_module)
    processor = requests.get_extra_value(request, f"processor_cn_{i}", default_model)
    model = requests.get_extra_value(request, f"model_cn_{i}", "")
    img = lib.valid_base64(image_b64)
    if not img and not model:
        # 部分处理器可以不用image
        return unit

    # processor_res
    if img:
        unit["processor_res"] = min(max(img.size[0:2]), 512)

    unit["module"] = processor
    unit["model"] = model
    unit["image"] = image_b64
    unit["enabled"] = True
    return unit


def get_cn_tile_unit(p):
    unit = _get_cn_empty_unit()
    if not requests.get_extra_value(p, "scale_by_tile", False):
        return unit

    unit["module"] = default_tile_module
    unit["model"] = default_tile_model
    unit["enabled"] = True
    unit["image"] = ""
    return unit


def _get_cn_empty_unit():
    # 参数在 ControlNetUnit 不同版本中默认值不一样，这里统一一下，目前兼容至 1.1.220
    return {
        "model": "none",
        "module": "none",
        "enabled": False,
        "image": "",
        "processor_res": 512,
        "threshold_a": 64,
        "threshold_b": 64,
        "weight": 1.0,
        "guidance_start": 0.0,
        "guidance_end": 1.0,
    }


def _to_process_unit(unit):
    if unit["enabled"]:
        unit["model"] = _find_closest_cn_model_name(unit["model"])

    return external_code.ControlNetUnit(**unit)

