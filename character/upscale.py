from character.lib import log

NAME = "AutoUpscale"

def apply_auto_upscale(request):
    auto_upscale = getattr(request, "character_auto_upscale", False)
    if not auto_upscale:
        return

    request.alwayson_scripts.update({NAME: {'args': [True]}})

