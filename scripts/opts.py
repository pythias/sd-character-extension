import sys
from character.lib import log
from modules import shared

updated_options = {
    'control_net_no_detectmap': True,
    'control_net_max_models_num': 3,
    'interrogate_keep_models_in_memory': True,
    'interrogate_clip_num_beams': 1,
    'interrogate_clip_skip_categories': [],
    'interrogate_clip_min_length': 24,
    'interrogate_clip_max_length': 48,
    'interrogate_return_ranks': True,
}

shared.opts.data.update(updated_options)

# for key, value in updated_options.items():
#     shared.opts.set(key, value)

if shared.cmd_opts.nowebui:
    from modules.paths_internal import extensions_builtin_dir
    sys.path.append(extensions_builtin_dir)
    sys.path.append(os.path.join(extensions_builtin_dir, "Lora"))
    from Lora import extra_networks_lora

    from modules import extra_networks, extra_networks_hypernet
    extra_networks.register_extra_network(extra_networks_lora.ExtraNetworkLora())
    extra_networks.register_extra_network(extra_networks_hypernet.ExtraNetworkHypernet())

    log("Extra networks has been registered.")    

log("Options has been set.")
