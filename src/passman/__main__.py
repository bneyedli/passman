"""
Lazy catch and redirect to console
"""
import sys

if __name__ == "__main__":
    from passman.console.app import main

    sys.exit(main())
