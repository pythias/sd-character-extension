# api endpoints
from character.lib import keys_path, log, LogLevel
from character.models import *
from character.tables import *

from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5

from fastapi import FastAPI, APIRouter, FastAPI, Request
from fastapi.exceptions import HTTPException
from modules import script_callbacks as script_callbacks
from modules.api import api

import base64
import character.lib as character
import gradio as gr
import time

code_error = 100001
code_invalid_input = 100002
code_missing_signature = 100003
code_invalid_signature_name = 100004
code_expired_signature = 100005
code_invalid_signature = 100006
code_not_found = 100404
code_character_permission_denied = 100007
code_character_not_exists = 100008
code_character_already_exists = 100009
code_character_was_blank = 100010

fashion_table = FashionTable()
pose_table = PoseTable()

class ApiException(HTTPException):
    def __init__(
        self,
        code,
        message,
        status_code: int = 200,
    ) -> None:
        self.code = code
        self.message = message
        super().__init__(status_code=status_code)


class ApiHijack(api.Api):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_api_route("/character/v1/txt2img", self.character_txt2img, methods=["POST"])
        self.add_api_route("/character/v1/img2img", self.character_img2img, methods=["POST"])

    def character_txt2img(self, request: CharacterTxt2ImgRequest):
        args = vars(request)
        lightRequest = CharacterTxt2Img(**args)
        return self.text2imgapi(lightRequest.to_full())

    def character_img2img(self, request: CharacterTxt2ImgRequest):
        args = vars(request)
        lightRequest = CharacterTxt2Img(**args)
        return self.text2imgapi(lightRequest.to_full())

api.Api = ApiHijack

def characterAPI(_: gr.Blocks, app: FastAPI):
    @app.get('/character/v1/status')
    def status():
        return {"online": True}

    @app.get('/character/v1/poses')
    def poses():
        return pose_table.poses

    @app.get('/character/v1/fashions')
    def fashions():
        return fashion_table.fashions

    @app.middleware("http")
    async def verify_signature(request: Request, call_next):
        if request.url.path.startswith("/docs") or request.url.path.startswith("/openapi.json"):
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

script_callbacks.on_app_started(characterAPI)
log("API loaded")
