from character.lib import log, version_flag
from character.metrics import cImages, iCharacter, totalMemory, gpuDriver

from fastapi import FastAPI, Request

from starlette.routing import Route
from starlette.responses import PlainTextResponse
from prometheus_client import generate_latest

from modules import script_callbacks, shared

import time
import torch

def metrics_api(_, app: FastAPI):
    @app.get('/character/meta/status', tags=["Status"])
    def status():
        return {
            "name": shared.cmd_opts.character_server_name,
            "version": version_flag,
            "online": True,
            "images": cImages.collect()[0].samples[0].value,
            "memory_allocated": torch.cuda.memory_allocated(),
            "max_memory_allocated": torch.cuda.max_memory_allocated(),
        }

    @app.get('/character/meta/metrics', tags=["Status"])
    def metrics():
        metrics_data = generate_latest()
        return PlainTextResponse(metrics_data, media_type="text/plain")

    @app.middleware("http")
    async def log_time(req: Request, call_next):
        if req.url.path.startswith('/character/meta'):
            return await call_next(req)

        ts = time.time()
        res = await call_next(req)
        duration = str(round(time.time() - ts, 3))
        
        log('API {method} {endpoint} {duration} {code}'.format(
            code = res.status_code,
            method = req.scope.get('method', '-'),
            endpoint = req.scope.get('path', '-'),
            duration = duration,
        ))
        return res

    try:
        iCharacter.info({
            'version': version_flag,
            'name': shared.cmd_opts.character_server_name,
            'driver': f"{gpuDriver}",
            'total_gpu_memory': f"{totalMemory}",
        })
    except Exception as e:
        pass

    log("Metrics loaded")

script_callbacks.on_app_started(metrics_api)
