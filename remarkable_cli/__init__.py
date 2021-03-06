# -*- coding: utf-8 -*-
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from os import path
from .client import Client

name = "remarkable-cli"
__version__ = "0.1.1"
__all__ = ["main"]


def main():
    parser = ArgumentParser(
        "remarkable-cli",
        description="A CLI for interacting with the Remarkable paper tablet.",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--version", action="version", version="%(prog)s " + __version__
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="logging verbosity level",
        action="count",
        default=3,
    )
    parser.add_argument(
        "-a",
        "--action",
        help="backup actions to perform on reMarkable tablet",
        action="append",
        type=str,
        choices=["push", "pull", "clean-local"],
    )

    device_group = parser.add_argument_group("reMarkable device")
    device_group.add_argument(
        "-d",
        "--destination",
        help="reMarkable tablet network destination hostname",
        type=str,
        default="10.11.99.1",
    )
    device_group.add_argument(
        "-p",
        "--port",
        help="reMarkable tablet network destination port",
        type=int,
        default=22
    )
    device_group.add_argument(
        "-u",
        "--username",
        help="reMarkable tablet ssh user",
        type=str,
        default="root",
    )
    device_group.add_argument(
        "--password",
        help="reMarkable ssh connection password",
        type=str,
        default=None
    )
    device_group.add_argument(
        "-f",
        "--file-path",
        type=str,
        help="reMarkable directory containing xochitl files",
        default="/home/root/.local/share/remarkable/xochitl/"
    )

    local_group = parser.add_argument_group("local")
    local_group.add_argument(
        "-b",
        "--backup-dir",
        help="local machine backup directory",
        type=str,
        default=path.join(path.expanduser("~"), "reMarkable"),
    )

    args = parser.parse_args()

    if not args.action:
        # no action specified, display the help message
        parser.print_help()
        return

    c = Client(args)
    c.run_actions()
