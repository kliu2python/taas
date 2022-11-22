import os

from taascli.conf import load_config
from taascli.utils import PrintInColor
from taascli.params import parser


def _run():
    args = None
    try:
        args = parser.parse_args()
    except TypeError:
        PrintInColor.red("Missing Parameters!")
        parser.parse_args(["-h"])

    load_config()

    if hasattr(args, "func"):
        args.func(args)
    else:
        PrintInColor.red(
            "specified parameter has no operation defined, please check usage"
        )
        parser.parse_args(["-h"])


def main():
    debug = os.environ.get("DEBUG", "False") == "True"
    try:
        _run()
    except Exception as e:
        PrintInColor.red(f"Error when execute: {e}")
        if debug:
            raise e
