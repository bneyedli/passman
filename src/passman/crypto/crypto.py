"""
Utility classes for managing crypto functions
"""
import logging
from datetime import datetime, timedelta
from getpass import getpass
from json import dumps as json_dumps
from json import loads as json_loads
from os import environ, listdir
from os.path import dirname
from os.path import exists as path_exists
from pathlib import Path

from dateutil.parser import parse as date_parser
from gnupg import GPG
from pyotp import TOTP


class Crypto:
    """
    Interface to gpg and encryption and decryption methods for secrets management
    """

    def __init__(self, run_args):
        self.logger = logging.getLogger(__name__)
        user_home = environ.get("HOME")
        self.args = {
            "crypt_home": run_args.crypt_home,
            "account_home": run_args.crypt_home + "/passman/" + run_args.account,
            "secret_type": run_args.secret_type,
            "vendor": run_args.vendor,
        }
        self.gpg = GPG(gnupghome=f"{user_home}/.gnupg")
        self.file = (
            f"{self.args['account_home']}/"
            f"{self.args['vendor']}-{self.args['secret_type']}.gpg"
        )
        self.max_secret_age = {
            "soft": 60,
            "hard": 90,
        }
        self.secrets = [
            secret.split("-")[0]
            for secret in listdir(self.args["account_home"])
            if secret.endswith(f"{self.args['secret_type']}.gpg")
        ]

    def decrypt_file(self):
        """
        Check if file exists, decrypt and copy to clipboard
        """
        if path_exists(self.file):
            self.logger.debug("File to decrypt: %s exists", self.file)
        else:
            self.logger.error("File doesn't exist: %s", self.file)
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
            self.logger.info("File to encrypt: %s already exists", self.file)
            raise SystemExit(1)

        if path_exists(parent_dir):
            self.logger.debug("Parent directory: %s exists!", parent_dir)
        else:
            self.logger.debug("Creating parent directory: %s ", parent_dir)
            Path(parent_dir).mkdir(parents=True, exist_ok=False)

        Path(self.file).touch(mode=0o600, exist_ok=False)
        private_keys = self.gpg.list_keys(True)
        recipients = []
        for key in private_keys:
            fingerprint = key["fingerprint"]
            recipients.append(fingerprint)
        recipients = set(recipients)
        secret_meta = {}
        if self.args["secret_type"] == "passphrase":  # nosec - not a hardcoded secret
            secret_meta["user_id"] = input("Enter user id: ")
        secret_meta["secret"] = getpass(prompt="Enter secret value: ")
        secret_meta["genesis"] = datetime.utcnow().isoformat()
        encrypted_file = self.gpg.encrypt(
            json_dumps(secret_meta), output=self.file, recipients=recipients
        )

        if encrypted_file.status == "encryption ok":
            self.logger.info("Success")

    def generate_otp(self, secret: str) -> str:
        """
        Generate and verify OTP from given secret
        """
        totp = TOTP(secret)
        code = totp.now()
        if not totp.verify(code):
            self.logger.error("Unable to verify TOTP")
            raise SystemExit(1)

        return code

    def check_age(self, secret_genesis: str) -> None:
        """
        Check age of secret and warn if out of compliance
        """
        secret_genesis = date_parser(secret_genesis)
        secret_max_age_soft = secret_genesis + timedelta(
            days=self.max_secret_age["soft"]
        )
        secret_max_age_hard = secret_genesis + timedelta(
            days=self.max_secret_age["hard"]
        )
        time_now = date_parser(datetime.utcnow().isoformat())

        time_delta = time_now - secret_genesis

        if time_now > secret_max_age_soft:
            self.logger.info(  # nosemgrep
                "Secret age: %s exceeds soft limit: %s",
                time_delta,
                secret_max_age_soft,
            )
            password_valid = True
        elif time_now > secret_max_age_hard:
            self.logger.info(  # nosemgrep
                "Rotate secret! secret age: %s exceeds hard limit: %s",
                time_delta,
                secret_max_age_hard,
            )
            password_valid = False
        else:
            self.logger.debug("Password age is good")
            password_valid = True

        return password_valid
