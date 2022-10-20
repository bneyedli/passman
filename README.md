# Usage
```
usage: pman [-h] (--read | --write | --list) [--account ACCOUNT] --vendor VENDOR [--secret-type {passphrase,token,otp}] [--crypt-home CRYPT_HOME]

Encrypt and decrypt password files on filesystems like kbfs.

options:
  -h, --help            show this help message and exit
  --read                Read passphrase
  --write               Write passphrase
  --list                List vendors for given account
  --account ACCOUNT     Host or ip to target and path, default: default
  --vendor VENDOR       Vendor of stored secret
  --secret-type {passphrase,token,otp}
                        Type of secret, default: passphrase
  --crypt-home CRYPT_HOME
                        Path to root of encrypted filesystem default: ${HOME}/.crypt
```
