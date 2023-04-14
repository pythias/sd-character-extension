import argparse


def preload(parser: argparse.ArgumentParser):
    parser.add_argument("--character-host", type=str, default="api.character.io", help="Character service host")
