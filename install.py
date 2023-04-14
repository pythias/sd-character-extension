import launch
import os

req_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "requirements.txt")

with open(req_file) as file:
    for lib in file:
        lib = lib.strip()
        if launch.is_installed(lib):
            continue
        
        launch.run_pip(f"install {lib}", f"sd-character-extension requirement: {lib}")
