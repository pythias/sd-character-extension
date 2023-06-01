from character.lib import log
from modules import shared

shared.opts.set('control_net_no_detectmap', True)
shared.opts.set('control_net_max_models_num', 3)

shared.opts.set('interrogate_keep_models_in_memory', True)
shared.opts.set('interrogate_clip_num_beams', 1)
shared.opts.set('interrogate_clip_skip_categories', [])
shared.opts.set('interrogate_clip_min_length', 24)
shared.opts.set('interrogate_clip_max_length', 48)

log("Options has been set.")
