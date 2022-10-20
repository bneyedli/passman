#!/usr/bin/env python3
"""
Module to write or retrieve encrypted secrets from encrypted filesystem
"""

import logging
from getpass import getpass
from json import dumps as json_dumps
from json import loads as json_loads
from os import environ
from os.path import dirname
from os.path import exists as path_exists
from pathlib import Path

from gnupg import GPG
from parseargs import ParseArgs
from pyotp import TOTP
from pyperclip import copy as clipboard_copy
from trapper import Trapper

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)


class Crypto:
    """
    Interface to gpg and encryption and decryption methods for secrets management
    """

    def __init__(self, run_args):
        user_home = environ.get("HOME")
        self.gpg = GPG(gnupghome=f"{user_home}/.gnupg")
        self.file = (
            f"{run_args.crypt_home}/passman/"
            f"{run_args.account}/{run_args.vendor}-{run_args.secret_type}.gpg"
        )

    def decrypt_file(self):
        """
        Check if file exists, decrypt and copy to clipboard
        """
        if path_exists(self.file):
            logger.debug("File to decrypt: %s exists", self.file)
        else:
            logger.error("File doesn't exist: %s", self.file)
            raise SystemExit(1)

        with open(self.file, "rb") as encrypted_file:
            file = self.gpg.decrypt(encrypted_file.read())
            secret_meta = json_loads(file.data)

        return secret_meta

    def encrypt_file(self):
        """
        Check if file and directory exist, take input, encrypt and write to filesystem
        """
        parent_dir = dirname(self.file)
        if path_exists(self.file):
            logger.info("File to encrypt: %s already exists", self.file)
            raise SystemExit(1)

        if path_exists(parent_dir):
            logger.debug("Parent directory: %s exists!", parent_dir)
        else:
            logger.debug("Creating parent directory: %s ", parent_dir)
            Path(parent_dir).mkdir(parents=True, exist_ok=False)

        Path(self.file).touch(mode=0o600, exist_ok=False)
        private_keys = self.gpg.list_keys(True)
        recipients = []
        for key in private_keys:
            fingerprint = key["fingerprint"]
            recipients.append(fingerprint)
        recipients = set(recipients)
        secret_meta = {}
        secret_meta["user_id"] = input("Enter user id: ")
        secret_meta["secret"] = getpass(prompt="Enter password: ")
        encrypted_file = self.gpg.encrypt(
            json_dumps(secret_meta), output=self.file, recipients=recipients
        )

        if encrypted_file.status == "encryption ok":
            logger.info("Success")

    def generate_otp(self, secret: str) -> str:
        """
        Generate and verify OTP from given secret
        """
        totp = TOTP(secret)
        code = totp.now()
        if not totp.verify(code):
            logger.error("Unable to verify TOTP")
            raise SystemExit(1)

        return code


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
            "action": "store_true",
            "help": "Read passphrase",
            "exclusive_group": "action",
        },
        {
            "switch": "--write",
            "action": "store_true",
            "help": "Write passphrase",
            "exclusive_group": "action",
        },
        {
            "switch": "--list",
            "action": "store_true",
            "help": "List vendors for given account",
            "exclusive_group": "action",
        },
        {
            "switch": "--account",
            "default": "default",
            "help": "Host or ip to target and path, default: default",
            "type": str,
        },
        {
            "switch": "--vendor",
            "help": "Vendor of stored secret",
            "default": None,
            "type": str,
            "required": True,
        },
        {
            "switch": "--secret-type",
            "default": "passphrase",
            "help": "Type of secret, default: passphrase",
            "choices": ["passphrase", "token", "otp"],
            "type": str,
        },
        {
            "switch": "--crypt-home",
            "default": f"{home}/.crypt",
            "help": f"Path to root of encrypted filesystem default: {home}/.crypt",
            "type": str,
        },
    ]

    parser = ParseArgs(app_metadata["name"], app_metadata["description"], app_arguments)
    args = parser.args_parsed

    crypto = Crypto(args)

    if args.read:
        secret_meta = crypto.decrypt_file()
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


if __name__ == "__main__":
    main()
