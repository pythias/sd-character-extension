from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

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
code_character_api_only = 100011
code_character_nsfw = 100012

code_character_unknown_algorithm = 100101

class ApiException(HTTPException):
    def __init__(
        self,
        code,
        message,
        status_code: int = 400,
    ) -> None:
        self.code = code
        self.message = message
        super().__init__(status_code=status_code)

    def response(self):
        err = {
            "code": vars(self).get('code', ''),
            "message": vars(self).get('message', ''),
        }
        return JSONResponse(status_code=vars(self).get('status_code', 400), content=jsonable_encoder(err))

    @staticmethod
    def fromException(e):
        return ApiException(code_error, str(e))


def missing_signature():
    return ApiException(code_missing_signature, "Missing signature").response()

def invalid_signature_name():
    return ApiException(code_invalid_signature_name, "Invalid signature name").response()

def mismatched_signature():
    return ApiException(code_invalid_signature, "Invalid signature").response()

def nsfw():
    return ApiException(code_character_nsfw, "nsfw").response()

def raise_nsfw():
    raise ApiException(code_character_nsfw, "nsfw")

