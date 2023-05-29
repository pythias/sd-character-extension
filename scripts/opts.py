from character.lib import log
from modules import shared

shared.opts.data.update({
    'control_net_no_detectmap': True,
    'control_net_max_models_num': 3,
})

# shared.opts.interrogate_clip_skip_categories
# shared.opts.interrogate_clip_num_beams
# shared.opts.interrogate_clip_min_length
# shared.opts.interrogate_clip_max_length

log("Options loaded")