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

def signature_api(_: gr.Blocks, app: FastAPI):
    @app.middleware("http")
    async def signature_middleware(request: Request, call_next):
        for prefix in ignore_prefixes:
            if request.url.path.startswith(prefix):
                return await call_next(request)

        if shared.cmd_opts.character_api_only and not request.url.path.startswith("/character"):
            raise ApiException(code_character_api_only, "character api only.")

        if shared.cmd_opts.character_ignore_signature:
            return await call_next(request)

        sign = request.headers.get('X-Signature', '')
        sign_name = request.headers.get('X-Signature-Name', 'my')
        sign_timestamp = request.headers.get('X-Signature-Time', '')

        if not sign or not sign_name or not sign_timestamp:
            raise ApiException(code_missing_signature, "signature is missing.")

        key_path = os.path.join(keys_path, f"{sign_name}_rsa_public.pem")
        if not os.path.exists(key_path):
            raise ApiException(code_invalid_signature, "signature name is invalid.")

        with open(key_path, mode='rb') as pem_file:
            key_data = pem_file.read()

        verifier = PKCS1_v1_5.new(RSA.importKey(key_data.strip()))

        if (int(sign_timestamp) + 60) < int(time.time()):
            raise ApiException(code_expired_signature, "signature was expired.")

        body_bytes = await request.body()
        data_value = body_bytes.decode() + sign_timestamp
        data_hash = SHA256.new(data_value.encode('utf-8'))
        sign_decoded = base64.b64decode(sign)

        if not verifier.verify(data_hash, sign_decoded):
            log(f"Signature is mismatch. sign_name={sign_name}", LogLevel.ERROR)
            raise ApiException(code_invalid_signature, "signature is mismatch.")

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
