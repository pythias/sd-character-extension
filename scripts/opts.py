import sys
import os
from character import lib
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
    }

    shared.opts.data.update(updated_options)

    if not lib.is_webui():
        from modules.paths_internal import extensions_builtin_dir

        sys.path.append(extensions_builtin_dir)
        sys.path.append(os.path.join(extensions_builtin_dir, "Lora"))
        from Lora import extra_networks_lora

        from modules import extra_networks, extra_networks_hypernet
        extra_networks.register_extra_network(extra_networks_lora.ExtraNetworkLora())
        extra_networks.register_extra_network(extra_networks_hypernet.ExtraNetworkHypernet())

        lib.log(f"Extra networks has been registered, networks:{extra_networks.extra_network_registry}")

    lib.log("Options has been set.")

script_callbacks.on_app_started(update_options)