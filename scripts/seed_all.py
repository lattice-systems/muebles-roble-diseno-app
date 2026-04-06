"""Ejecuta el pipeline completo de seeds en el orden oficial.

Uso:
    venv/bin/python scripts/seed_all.py
    venv/bin/python scripts/seed_all.py --without-users
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

BASE_SEED_ORDER = [
    "seed_units.py",
    "seed_raw_materials.py",
    "seed_wood_types.py",
    "seed_products.py",
    "seed_product_colors.py",
    "seed_payment_methods.py",
    "seed_purchase.py",
    "seed_bom.py",
    "seed_inventory.py",
]

RBAC_SEED = "seed_users_by_role.py"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ejecuta todos los seeds oficiales en una sola corrida."
    )
    parser.add_argument(
        "--without-users",
        action="store_true",
        help="Omite el seed de usuarios RBAC.",
    )
    return parser.parse_args()


def _run_seed_script(scripts_dir: Path, script_name: str) -> None:
    script_path = scripts_dir / script_name
    if not script_path.exists():
        raise FileNotFoundError(f"No existe el script requerido: {script_path}")

    print(f"\n>>> Ejecutando {script_name} ...")
    started_at = time.perf_counter()
    subprocess.run([sys.executable, str(script_path)], check=True)
    elapsed = time.perf_counter() - started_at
    print(f"<<< OK {script_name} ({elapsed:.1f}s)")


def main() -> int:
    args = _parse_args()
    scripts_dir = Path(__file__).resolve().parent

    seed_order = list(BASE_SEED_ORDER)
    if not args.without_users:
        seed_order.append(RBAC_SEED)

    print("Iniciando pipeline de seeds...")
    print(f"Python: {sys.executable}")
    print("Orden de ejecucion:")
    for script_name in seed_order:
        print(f"- {script_name}")

    pipeline_started_at = time.perf_counter()

    try:
        for script_name in seed_order:
            _run_seed_script(scripts_dir, script_name)
    except subprocess.CalledProcessError as exc:
        failed_script = Path(exc.cmd[-1]).name if exc.cmd else "desconocido"
        print(f"\nERROR: fallo {failed_script} con exit code " f"{exc.returncode}.")
        return exc.returncode or 1
    except FileNotFoundError as exc:
        print(f"\nERROR: {exc}")
        return 1

    total_elapsed = time.perf_counter() - pipeline_started_at
    print(f"\nPipeline de seeds completado en {total_elapsed:.1f}s.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
