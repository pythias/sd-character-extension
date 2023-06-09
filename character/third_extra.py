import sys
import os
from character import lib
from modules import extra_networks

def load_extras():
    if lib.is_webui():
        return

    extra_networks.initialize()
    extra_networks.register_default_extra_networks()

    from modules.paths_internal import extensions_builtin_dir
    sys.path.append(extensions_builtin_dir)
    sys.path.append(os.path.join(extensions_builtin_dir, "Lora"))
    from Lora import extra_networks_lora
    extra_networks.register_extra_network(extra_networks_lora.ExtraNetworkLora())

    lib.log(f"Extras has been loaded, extra_networks: {extra_networks.extra_network_registry.keys()}")