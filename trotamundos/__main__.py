"""Arranque de una región: `python -m trotamundos [--puerto 8000]`."""

from __future__ import annotations

import argparse
import logging

import uvicorn

from trotamundos.app import crear_app
from trotamundos.config import Config


def main() -> None:
    parser = argparse.ArgumentParser(description="Servidor de una región de Trotamundos")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--puerto", type=int, default=8000)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    uvicorn.run(crear_app(Config()), host=args.host, port=args.puerto, log_level="info")


if __name__ == "__main__":
    main()
