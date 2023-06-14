from character import lib, names

def is_debug(request):
    return get_extra_value(request, "debug", False)

def from_webui(request):
    return get_extra_value(request, names.ParamFromUI, True)

def set_request_from_api(request):
    update_extra(request, names.ParamFromUI, False)

def multi_enabled(request):
    return get_extra_value(request, names.ParamMultiEnabled, False)

def set_multi_count(request, count):
    update_extra(request, names.ParamMultiCount, count)

def get_multi_count(request):
    return get_extra_value(request, names.ParamMultiCount, 1)

def set_has_illegal_words(request):
    update_extra(request, names.ExtraHasIllegalWords, True)

def has_illegal_words(request):
    return get_extra_value(request, names.ExtraHasIllegalWords, False)

def get_cn_image(request):
    return get_extra_value(request, names.ParamLineArt, "")

def get_pose_image(request):
    return get_extra_value(request, names.ParamPose, "")

def get_i2i_image(request):
    return get_extra_value(request, names.ParamImage, "")

def extra_init(request):
    request.extra_generation_params.setdefault(names.Name, {})
    extra = get_value(request, names.ParamExtra, {})
    if isinstance(extra, dict):
        request.extra_generation_params[names.Name].update(extra)
    else:
        lib.log(f"extra is not dict, {type(extra)}")

    # delete extra
    if hasattr(request, names.ParamExtra):
        del request.character_extra

    # 对老版本请求的兼容
    # character_image -> cn_image
    # character_input_image -> i2i_image
    cn_image_base64 = get_value(request, "character_image", "")
    if cn_image_base64 != "":
        update_extra(request, names.ParamLineArt, cn_image_base64)
    
    i2i_image_base64 = get_value(request, "character_input_image", "")
    if i2i_image_base64 != "":
        update_extra(request, names.ParamImage, i2i_image_base64)

    set_request_from_api(request)


def update_extra(request, key, value):
    update_extras(request, {key: value})


def update_extras(request, values):
    request.extra_generation_params.setdefault(names.Name, {})
    request.extra_generation_params[names.Name].update(values)


def clear_temporary_extras(request):
    """
    瘦身，清除临时参数
    """
    for key in list(request.extra_generation_params[names.Name].keys()):
        if key.startswith("image_"):
            del request.extra_generation_params[names.Name][key]


def get_extra_value(request, key, default):
    """
    获取自定义参数的值
    """
    character_extra = get_value(request, names.ParamExtra, None)
    if character_extra is None:
        extra = get_value(request, "extra_generation_params", {})
        character_extra = get_value(extra, names.Name, {})
    
    return get_value(character_extra, key, default)


def update_script_args(p, name, args):
    if hasattr(p, 'scripts'):
        _update_script_args(p, name, args)
    else:
        _update_request_scripts(p, name, args)

def _update_request_scripts(request, name, args):
    # 接口请求数据处理
    request.alwayson_scripts.update({name: {'args': args}})

def _update_script_args(p, name, args):
    # 过程中参数处理
    if p.scripts is None or not hasattr(p.scripts, 'alwayson_scripts'):
        return

    for s in p.scripts.alwayson_scripts:
        if s.title().lower() == name.lower():
            script_args = list(p.script_args)
            if len(args) > s.args_to - s.args_from:
                script_args[s.args_from:s.args_from] = args[:s.args_to - s.args_from]
            elif len(args) < s.args_to - s.args_from:
                script_args[s.args_from:s.args_from+len(args)] = args
            else:
                script_args[s.args_from:s.args_to] = args
            
            p.script_args = tuple(script_args)
            break

get_value = lib.get_or_default