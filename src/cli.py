"""
Unified Enterprise Bench CLI Facade
===================================
Backward-compatible entrypoint forwarding to the modular src.cli package.
"""

from __future__ import annotations

from src.cli import app


def main():
    app()


if __name__ == "__main__":
    main()
