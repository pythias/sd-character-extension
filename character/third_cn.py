import os
import sys

from character import lib, requests, names
from modules.paths_internal import extensions_dir
sys.path.append(os.path.join(extensions_dir, "sd-webui-controlnet"))
from scripts import external_code, global_state, controlnet_version

control_net_models = external_code.get_models(update=True)
control_net_version = controlnet_version.version_flag

def _find_closest_cn_model_name(search):
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

lib.log(f"ControlNet {control_net_version} loaded, models: {len(control_net_models)}, lineart: {_find_closest_cn_model_name('lineart')}")

def apply_args(request):
    units = []
    units.append(_get_cn_image_unit(request, 0, "lineart_realistic", "lineart"))
    for i in range(1, 5):
        units.append(_get_cn_image_unit(request, i))

    requests.update_script_args(request, "ControlNet", [_to_process_unit(unit) for unit in units])

def _get_cn_image_unit(request, i, default_preprocessor = None, default_model = None):
    model = requests.get_extra_value(request, f"model_cn_{i}", default_model)
    model = _find_closest_cn_model_name(model)
    if not model:
        return _get_cn_disabled_unit()

    image_b64 = requests.get_extra_value(request, f"image_cn_{i}", None)

    unit = _get_cn_empty_unit()
    unit["module"] = requests.get_extra_value(request, f"processor_cn_{i}", default_preprocessor)
    unit["model"] = model
    unit["image"] = image_b64

    # todo 特殊场景的处理，比如inpainting的mask

    # 参数: processor_res, 以传递的参数为主, 但是如果没有传递参数, 则使用默认值/或者图像的尺寸
    processor_res = requests.get_extra_value(request, f"processor_res_cn_{i}", None)
    if processor_res is None:
        img = lib.valid_base64(image_b64)
        if img:
            unit["processor_res"] = min(max(img.size[0:2]), 512)

    # 其他参数
    _fill_unit_with_extra(unit, request, i)

    return unit


def _get_cn_disabled_unit():
    return {
        "enabled": False,
    }


def _fill_unit_with_extra(unit, request, index):
    names = ["weight", "resize_mode", "low_vram", "threshold_a", "threshold_b", "guidance_start", "guidance_end", "pixel_perfect", "control_mode"]
    for name in names:
        value = requests.get_extra_value(request, f"{name}_cn_{index}", None)
        if value is not None:
            unit[name] = value


def _get_cn_empty_unit():
    # 参数在 ControlNetUnit 不同版本中默认值不一样，这里统一一下，目前兼容至 1.1.220
    # enabled: bool=True,
    # module: Optional[str]=None,
    # model: Optional[str]=None,
    # weight: float=1.0,
    # image: Optional[InputImage]=None,
    # resize_mode: Union[ResizeMode, int, str] = ResizeMode.INNER_FIT,
    # low_vram: bool=False,
    # processor_res: int=-1,
    # threshold_a: float=-1,
    # threshold_b: float=-1,
    # guidance_start: float=0.0,
    # guidance_end: float=1.0,
    # pixel_perfect: bool=False,
    # control_mode: Union[ControlMode, int, str] = ControlMode.BALANCED,
    return {
        "enabled": True,
        "module": None,
        "model": None,
        "weight": 1.0,
        "image": "",
        "resize_mode": 1,
        "processor_res": 512,
        "threshold_a": 64,
        "threshold_b": 64,
        "guidance_start": 0.0,
        "guidance_end": 1.0,
        "pixel_perfect": False,
        "control_mode": 1,
    }


def _to_process_unit(unit):
    return external_code.ControlNetUnit(**unit)

