from character.lib import log

from modules import script_callbacks

def upscale_api(_, app: FastAPI):
    @app.get('/character/v2/upscale', tags=["Character"])
    def upscale():
        return {"todo": True}


script_callbacks.on_app_started(upscale_api)

log("upscale_api loaded")