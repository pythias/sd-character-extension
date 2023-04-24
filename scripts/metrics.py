from character.lib import log
from fastapi import FastAPI
from prometheus_client import make_asgi_app
from modules import script_callbacks

def metrics_api(_, app: FastAPI):
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

script_callbacks.on_app_started(metrics_api)

log("Tags loaded")
