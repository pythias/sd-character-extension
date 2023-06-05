from character import lib, names


# todo 调整参数名字

def get_cn_image(request):
    return get_extra_value(request, "cn_image", "")

def get_pose_image(request):
    return get_extra_value(request, "pose_image", "")

def get_i2i_image(request):
    return get_extra_value(request, "i2i_image", "")

def extra_init(request):
    if isinstance(request, dict):
        request.setdefault('extra_generation_params', {})

    if not hasattr(request, 'extra_generation_params') or request.extra_generation_params is None:
        request.extra_generation_params = {}

    if names.Name not in request.extra_generation_params:
        request.extra_generation_params[names.Name] = {}

    extra = get_value(request, 'character_extra', {})
    if isinstance(extra, dict):
        request.extra_generation_params[names.Name].update(extra)

    # delete extra
    if hasattr(request, 'character_extra'):
        del request.character_extra

    # 对老版本请求的兼容
    # character_image -> cn_image
    # character_input_image -> i2i_image
    cn_image_base64 = get_value(request, "character_image", "")
    if cn_image_base64 != "":
        update_extra(request, "cn_image", cn_image_base64)
    
    i2i_image_base64 = get_value(request, "character_input_image", "")
    if i2i_image_base64 != "":
        update_extra(request, "i2i_image", i2i_image_base64)


def update_extra(request, key, value):
    request.extra_generation_params[names.Name].update({
        key: value,
    })


def update_extras(request, values):
    request.extra_generation_params[names.Name].update(values)


def get_extra_value(request, key, default):
    """
    获取自定义参数的值
    """
    character_extra = get_value(request, "character_extra", None)
    if character_extra is None:
        extra = get_value(request, "extra_generation_params", {})
        character_extra = get_value(extra, names.Name, {})
    
    return get_value(character_extra, key, default)


get_value = lib.get_or_default