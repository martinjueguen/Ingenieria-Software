"""Arranque de una región del despliegue multirregión activo-pasivo caliente (ADR-0012).

- Región primaria: atiende el tráfico, ejecuta workers y planificador, y replica
  su base OLTP a la de la secundaria después de cada transacción.
- Región secundaria: proceso caliente que responde heartbeats; no ejecuta
  procesos de fondo hasta que el Global Traffic Manager la promueve.

Uso:  python -m trotamundos.infraestructura.region --region primaria --puerto 8001
      python -m trotamundos.infraestructura.region --region secundaria --puerto 8002
"""

from __future__ import annotations

import argparse
import logging
import os

import uvicorn

from trotamundos.config import RAIZ


def configurar_entorno(region: str) -> None:
    var = RAIZ / "var"
    os.environ["TROTAMUNDOS_REGION"] = region
    os.environ["TROTAMUNDOS_BD"] = str(var / f"oltp-{region}.db")
    os.environ["TROTAMUNDOS_BUS"] = str(var / f"bus-{region}.db")
    if region == "primaria":
        os.environ["TROTAMUNDOS_REPLICA"] = str(var / "oltp-secundaria.db")
        os.environ.setdefault("TROTAMUNDOS_PROCESOS_FONDO", "1")
    else:
        os.environ["TROTAMUNDOS_REPLICA"] = ""
        os.environ["TROTAMUNDOS_PROCESOS_FONDO"] = "0"  # pasiva hasta ser promovida
        os.environ["TROTAMUNDOS_DATOS_DEMO"] = "0"      # sus datos llegan por replicación


def main() -> None:
    parser = argparse.ArgumentParser(description="Región de Trotamundos")
    parser.add_argument("--region", choices=["primaria", "secundaria"], required=True)
    parser.add_argument("--puerto", type=int, required=True)
    args = parser.parse_args()
    configurar_entorno(args.region)
    logging.basicConfig(level=logging.INFO, format=f"%(asctime)s [{args.region}] %(levelname)s %(name)s: %(message)s")

    from trotamundos.app import crear_app
    from trotamundos.config import Config

    uvicorn.run(crear_app(Config()), host="127.0.0.1", port=args.puerto, log_level="warning")


if __name__ == "__main__":
    main()
