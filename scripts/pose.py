from character.lib import log
from character.models import *
from character.tables import *

from fastapi import FastAPI
from modules import script_callbacks
from modules.api import api

import gradio as gr

def pose_app(_: gr.Blocks, app: FastAPI):
    @app.get('/character/v1/poses', tags=["Character"], response_model=List[PoseRow])
    def poses():
        return pose_table.poses

    @app.get('/character/v1/fashions', tags=["Character"], response_model=List[FashionRow])
    def fashions():
        return fashion_table.fashions

script_callbacks.on_app_started(pose_app)

log("Pose api loaded")
