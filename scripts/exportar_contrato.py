"""Regenera `specs/openapi.json` a partir de la API (ADR-0018).

Flujo spec-driven: primero se modifica el contrato/DTO, se revisa el diff de
`specs/openapi.json` en el PR y `tests/test_contratos.py` impide que la
implementación y el contrato diverjan.

Uso:  python -m scripts.exportar_contrato
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import replace

from trotamundos.app import crear_app
from trotamundos.config import RAIZ, Config


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        config = replace(Config(), ruta_bd=os.path.join(tmp, "a.db"), ruta_bus=os.path.join(tmp, "b.db"),
                         ruta_olap=os.path.join(tmp, "c.db"), ruta_replica="", procesos_fondo=False, datos_demo=False)
        app = crear_app(config)
        destino = RAIZ / "specs" / "openapi.json"
        destino.write_text(json.dumps(app.openapi(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        app.state.sistema.bd.cerrar()
        app.state.sistema.bus.bd.cerrar()
        app.state.sistema.almacen.bd.cerrar()
    print(f"Contrato actualizado: {destino}")


if __name__ == "__main__":
    main()
