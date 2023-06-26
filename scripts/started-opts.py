import sys
import os
from character import lib, third_extra, nsfw
from modules import shared, script_callbacks

def update_options(_, app):
    updated_options = {
        'control_net_no_detectmap': True,
        # 'control_net_max_models_num': 5, # ControlNet 初始化时已经决定，修改不起作用。需求修改config.json
        'interrogate_keep_models_in_memory': True,
        'interrogate_clip_num_beams': 1,
        'interrogate_clip_skip_categories': [],
        'interrogate_clip_min_length': 24,
        'interrogate_clip_max_length': 48,
        'interrogate_return_ranks': True,
        'face_editor_script_index': -3,
    }

    shared.opts.data.update(updated_options)
    lib.log("Options has been set")
    
    third_extra.load_extras()
    
    nsfw.load_models()
    lib.load_models()
        
script_callbacks.on_app_started(update_options)
