from character.lib import log
from fastapi import FastAPI
from starlette.routing import Route
from starlette.responses import PlainTextResponse
from prometheus_client import generate_latest

from modules import script_callbacks

def metrics_app(_, app: FastAPI):
    async def metrics_api(request):
        metrics_data = generate_latest()
        return PlainTextResponse(metrics_data, media_type="text/plain")

    app.add_route("/character/v1/metrics", metrics_api, methods=["GET"])

    @app.get('/character/v1/status1', tags=["Status"])
    def status():
        return {"online": True}


script_callbacks.on_app_started(metrics_app)

log("Metrics loaded")
