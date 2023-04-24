from character.lib import log
from fastapi import FastAPI
from starlette.routing import Route
from starlette.responses import PlainTextResponse
from prometheus_client import generate_latest

from modules import script_callbacks

def metrics_app(_, app: FastAPI):
    @app.get('/character/meta/status', tags=["Status"])
    def status():
        return {"online": True}

    @app.get('/character/meta/metrics', tags=["Status"])
    def metrics():
        metrics_data = generate_latest()
        return PlainTextResponse(metrics_data, media_type="text/plain")


script_callbacks.on_app_started(metrics_app)

log("Metrics loaded")
