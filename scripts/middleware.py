from character.lib import keys_path, log, set_request_id, version_flag
from character.errors import *

from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5

from uuid import uuid4
from fastapi import FastAPI, Request
from modules import script_callbacks, shared

import base64
import gradio as gr
import time
import os

ignore_prefixes = ["/docs",  "/openapi.json", "/character/meta"]

def setup_middleware(_: gr.Blocks, app: FastAPI):
    def signature_required(request: Request):
        # 文档和它的接口使用独立的Basic Auth
        for prefix in ignore_prefixes:
            if request.url.path.startswith(prefix):
                return False
            
        if shared.cmd_opts.nowebui:
            # require_prefixes = ["/character", "/sdapi", "/sd_extra_networks", "/controlnet", "/tagger"]
            # WebUI （非 API）不需要签名，使用Basic Auth
            return True
        
        # WebUI 仅用于测试
        return False


    @app.middleware("http")
    async def log_middleware(request: Request, call_next):
        request_id = str(uuid4())
        request_id = request_id.split('-')[-1]
        if request.url.path.startswith("/character/v2/"):
            set_request_id(request_id)

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Request-From"] = request.headers.get('X-Signature-Name', 'my')
        response.headers["X-Server-Name"] = shared.cmd_opts.character_server_name
        response.headers["X-Server-Version"] = version_flag
        return response


    @app.middleware("http")
    async def signature_middleware(request: Request, call_next):
        if not signature_required(request):
            return await call_next(request)

        sign = request.headers.get('X-Signature', '')
        sign_name = request.headers.get('X-Signature-Name', 'my')
        sign_timestamp = request.headers.get('X-Signature-Time', '')

        if not sign or not sign_name or not sign_timestamp:
            return ApiException(code_missing_signature, "signature is missing.").response()

        key_path = os.path.join(keys_path, f"{sign_name}_rsa_public.pem")
        if not os.path.exists(key_path):
            return ApiException(code_invalid_signature, "signature name is invalid.").response()

        with open(key_path, mode='rb') as pem_file:
            key_data = pem_file.read()

        verifier = PKCS1_v1_5.new(RSA.importKey(key_data.strip()))

        # if (int(sign_timestamp) + 60) < int(time.time()):
        #    return ApiException(code_expired_signature, "signature was expired.").response()

        body_bytes = await request.body()
        data_value = body_bytes.decode() + sign_timestamp
        data_hash = SHA256.new(data_value.encode('utf-8'))
        sign_decoded = base64.b64decode(sign)

        if not verifier.verify(data_hash, sign_decoded):
            return ApiException(code_invalid_signature, "signature is mismatch.").response()

        scope = request.scope
        receive = request.receive

        async def receive_with_body() -> dict:
            nonlocal body_bytes
            if body_bytes:
                result = {"type": "http.request", "body": body_bytes}
                body_bytes = None
            else:
                result = await receive()
            return result

        new_request = Request(scope, receive_with_body)
        return await call_next(new_request)

script_callbacks.on_app_started(setup_middleware)

log("Middleware loaded")
