#!/usr/bin/env python3
"""
Module to write or retrieve encrypted secrets from encrypted filesystem
"""

import logging
from os import environ

from pyperclip import copy as clipboard_copy

from passman.__version__ import __version__
from passman.config.parseargs import ParseArgs
from passman.crypto.crypto import Crypto
from passman.sys.trapper import Trapper

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)


def main():
    """
    Main function for cli invocation
    """
    home = environ.get("HOME")
    Trapper()
    app_metadata = {
        "name": "passman",
        "description": "Encrypt and decrypt password files on filesystems like kbfs.",
    }
    app_arguments = [
        {
            "switch": "--read",
            "flag": "-R",
            "action": "store_true",
            "help": "Read passphrase",
            "exclusive_group": "action",
        },
        {
            "switch": "--write",
            "flag": "-W",
            "action": "store_true",
            "help": "Write passphrase",
            "exclusive_group": "action",
        },
        {
            "switch": "--list",
            "flag": "-L",
            "action": "store_true",
            "help": "List vendors for given account",
            "exclusive_group": "action",
        },
        {
            "switch": "--version",
            "flag": "-V",
            "action": "store_true",
            "help": "Print application version",
            "exclusive_group": "action",
        },
        {
            "switch": "--account",
            "flag": "-a",
            "default": "default",
            "help": "Host or ip to target and path, default: default",
            "type": str,
        },
        {
            "switch": "--vendor",
            "flag": "-v",
            "help": "Vendor of stored secret",
            "default": None,
            "type": str,
        },
        {
            "switch": "--secret-type",
            "flag": "-t",
            "default": "passphrase",
            "help": "Type of secret, default: passphrase",
            "choices": ["passphrase", "token", "otp"],
            "type": str,
        },
        {
            "switch": "--crypt-home",
            "flag": "-H",
            "default": f"{home}/.crypt",
            "help": f"Path to root of encrypted filesystem default: {home}/.crypt",
            "type": str,
        },
    ]

    parser = ParseArgs(app_metadata["name"], app_metadata["description"], app_arguments)
    args = parser.args_parsed

    if (args.read or args.write) and args.vendor is None:
        if args.read:
            action = "--read"
        if args.write:
            action = "--write"
        parser.parser.error(f"\n\t--vendor is required for {action}")

    crypto = Crypto(args)

    if args.read:
        secret_meta = crypto.decrypt_file()
        if not crypto.check_age(secret_meta["genesis"]):
            raise SystemExit(1)
        if args.secret_type == "passphrase":  # nosec - not a hardcoded secret
            clipboard_copy(secret_meta["secret"])
            logger.info(
                "Secret copied to clipboard, user_id: %s", secret_meta["user_id"]
            )
        if args.secret_type == "otp":  # nosec - not a hardcoded secret
            ot_pass = crypto.generate_otp(secret_meta["secret"])
            clipboard_copy(ot_pass)
            logger.info("One time password copied to clipboard")

    elif args.write:
        crypto.encrypt_file()

    elif args.list:
        print(f"Listing secrets of type: {crypto.args['secret_type']}\n")
        for secret in crypto.secrets:
            print(secret)

    elif args.version:
        print(f"v{__version__}")


if __name__ == "__main__":
    main()
