from character.lib import log, version_flag

from fastapi import FastAPI, Request

from starlette.routing import Route
from starlette.responses import PlainTextResponse
from prometheus_client import generate_latest

from modules import script_callbacks

import gradio as gr
import time

def metrics_api(_, app: FastAPI):
    @app.get('/character/meta/status', tags=["Status"])
    def status():
        return {"online": True, "version": version_flag}

    @app.get('/character/meta/metrics', tags=["Status"])
    def metrics():
        metrics_data = generate_latest()
        return PlainTextResponse(metrics_data, media_type="text/plain")

    @app.middleware("http")
    async def log_time(req: Request, call_next):
        ts = time.time()
        res: Response = await call_next(req)
        duration = str(round(time.time() - ts, 3))
        
        log('API {method} {endpoint} {duration} {code}'.format(
            code = res.status_code,
            method = req.scope.get('method', '-'),
            endpoint = req.scope.get('path', '-'),
            duration = duration,
        ))
        return res

script_callbacks.on_app_started(metrics_api)

log("Metrics loaded")
