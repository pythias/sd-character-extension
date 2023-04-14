# loaded before parsing commandline args
import argparse
from modules.paths_internal import data_path

def preload(parser: argparse.ArgumentParser):
    parser.add_argument("--character-poses-file", type=str, default=os.path.join(data_path, 'character-poses.csv'))
    parser.add_argument("--character-fashions-file", type=str, default=os.path.join(data_path, 'fashions.csv'))