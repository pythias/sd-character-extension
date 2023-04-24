from character.lib import keys_path, log, LogLevel
from character.errors import *

from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5

from fastapi import FastAPI, Request
from modules import shared, script_callbacks

import base64
import gradio as gr
import time
import os

ignore_prefixes = ["/docs",  "/openapi.json", "/character/meta"]
require_prefixes = ["/character", "/sdapi"]

def signature_api(_: gr.Blocks, app: FastAPI):
    def signature_required(request: Request):
        if shared.cmd_opts.character_ignore_signature:
            return False

        for prefix in ignore_prefixes:
            if request.url.path.startswith(prefix):
                return False
    
        required = False
        for prefix in require_prefixes:
            if request.url.path.startswith(prefix):
                required = True
                break
        
        return required

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

        if (int(sign_timestamp) + 60) < int(time.time()):
            return ApiException(code_expired_signature, "signature was expired.").response()

        body_bytes = await request.body()
        data_value = body_bytes.decode() + sign_timestamp
        data_hash = SHA256.new(data_value.encode('utf-8'))
        sign_decoded = base64.b64decode(sign)

        if not verifier.verify(data_hash, sign_decoded):
            log(f"Signature is mismatch. sign_name={sign_name}", LogLevel.ERROR)
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

script_callbacks.on_app_started(signature_api)

log("Signature loaded")
