import argparse


def preload(parser: argparse.ArgumentParser):
    parser.add_argument("--character-server-name", type=str, default="Character", help="Character service name")
    parser.add_argument("--character-output-dir", type=str, default="/var/www/sd", help="Directory for save image")
    parser.add_argument("--character-short-name", type=str, default="sd01", help="Directory for save image")
    parser.add_argument("--character-host", type=str, default="https://sd/", help="Character host")