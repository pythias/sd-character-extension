import argparse


def preload(parser: argparse.ArgumentParser):
    parser.add_argument("--character-server-name", type=str, default="Character", help="Character service name")
    parser.add_argument("--character-ignore-signature", action='store_true', help="Ignore signature check")
    parser.add_argument("--character-api-only", action='store_true', help="Only use character api")
    parser.add_argument("--character-nsfw-filter", action='store_true', help="Filter nsfw images")
    
