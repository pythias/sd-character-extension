import sys
import os
from character import lib
from modules import extra_networks

enabled_extras = ["lora", "hypernet"]

# lora
if "lora" not in extra_networks.extra_network_registry:
    from modules.paths_internal import extensions_builtin_dir
    sys.path.append(extensions_builtin_dir)
    sys.path.append(os.path.join(extensions_builtin_dir, "Lora"))
    from Lora import extra_networks_lora
    extra_networks.register_extra_network(extra_networks_lora.ExtraNetworkLora())

# hypernet
if "hypernet" not in extra_networks.extra_network_registry:
    from modules import extra_networks_hypernet
    extra_networks.register_extra_network(extra_networks_hypernet.ExtraNetworkHypernet())

lib.log(f"Extra networks has been registered, networks:{extra_networks.extra_network_registry}")
