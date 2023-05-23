from character.lib import log
from modules import shared

shared.opts.data.update({
    'control_net_no_detectmap': True,
    'control_net_max_models_num': 3,
})

log("Options loaded")