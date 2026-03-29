"""
Servicio proxy para la API de COPOMEX.

Implementa caché en memoria para minimizar el consumo de créditos.
Solo se realiza una llamada a COPOMEX por código postal único.
"""

import logging
import re
import threading

import requests

logger = logging.getLogger(__name__)

# ── Configuración ──────────────────────────────────────────────────────
COPOMEX_TOKEN = "e74a76cd-2e9c-4155-84fb-ae2fd2004e86"
COPOMEX_BASE_URL = "https://api.copomex.com/query/info_cp"
REQUEST_TIMEOUT = 8  # segundos

# ── Caché en memoria (thread-safe) ────────────────────────────────────
_cache: dict[str, dict] = {}
_cache_lock = threading.Lock()
_pending_locks: dict[str, threading.Lock] = {}
_pending_meta_lock = threading.Lock()


class CopomexService:
    """Proxy hacia la API de COPOMEX con caché en memoria."""

    @staticmethod
    def lookup_cp(cp: str) -> dict | None:
        """
        Busca la información de un código postal.

        Args:
            cp: Código postal de 5 dígitos.

        Returns:
            dict con keys ``estado``, ``municipio``, ``colonias``
            o ``None`` si el CP es inválido / no se encontró.
        """
        # ── 1. Validación ──────────────────────────────────────────────
        if not cp or not re.fullmatch(r"\d{5}", cp.strip()):
            return None

        cp = cp.strip()

        # ── 2. Cache hit ───────────────────────────────────────────────
        with _cache_lock:
            if cp in _cache:
                logger.debug("COPOMEX cache HIT para CP %s", cp)
                return _cache[cp]

        # ── 3. Lock por CP para evitar requests duplicados simultáneos ─
        with _pending_meta_lock:
            if cp not in _pending_locks:
                _pending_locks[cp] = threading.Lock()
            cp_lock = _pending_locks[cp]

        with cp_lock:
            # Doble-check tras adquirir el lock
            with _cache_lock:
                if cp in _cache:
                    return _cache[cp]

            # ── 4. Llamada a COPOMEX ───────────────────────────────────
            try:
                url = f"{COPOMEX_BASE_URL}/{cp}"
                params = {"type": "simplified", "token": COPOMEX_TOKEN}

                logger.info("COPOMEX API CALL → CP %s", cp)
                response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
                response.raise_for_status()

                data = response.json()

                # El API devuelve {"error": true, ...} si el CP no existe
                if isinstance(data, dict) and data.get("error"):
                    logger.warning("COPOMEX: CP %s no encontrado", cp)
                    return None

                # Normalizar la respuesta
                result = CopomexService._parse_response(data, cp)
                if result:
                    with _cache_lock:
                        _cache[cp] = result
                    logger.info(
                        "COPOMEX cache STORED para CP %s (%d colonias)",
                        cp,
                        len(result["colonias"]),
                    )
                return result

            except requests.exceptions.Timeout:
                logger.error("COPOMEX timeout para CP %s", cp)
                return None
            except requests.exceptions.RequestException as exc:
                logger.error("COPOMEX request error para CP %s: %s", cp, exc)
                return None
            except Exception as exc:
                logger.error("COPOMEX error inesperado para CP %s: %s", cp, exc)
                return None

    @staticmethod
    def _parse_response(data: list | dict, cp: str) -> dict | None:
        """
        Extrae estado, municipio y lista de colonias de la respuesta COPOMEX.

        Formato simplificado de COPOMEX::

            {
                "error": false,
                "response": {
                    "cp": "37480",
                    "asentamiento": ["Colonia A", "Colonia B", ...],
                    "estado": "Guanajuato",
                    "ciudad": "León de los Aldama",
                    "municipio": "León",
                    "pais": "México"
                }
            }
        """
        try:
            # La respuesta simplificada envuelve todo en "response"
            if isinstance(data, dict) and "response" in data:
                info = data["response"]
            elif isinstance(data, dict):
                info = data
            else:
                return None

            estado = info.get("estado", "")
            # Preferir "municipio", fallback a "ciudad"
            municipio = info.get("municipio", "") or info.get("ciudad", "")

            # "asentamiento" puede ser una lista de strings o un solo string
            raw_colonias = info.get("asentamiento", [])
            if isinstance(raw_colonias, str):
                colonias = [raw_colonias] if raw_colonias else []
            elif isinstance(raw_colonias, list):
                colonias = [c for c in raw_colonias if isinstance(c, str) and c.strip()]
            else:
                colonias = []

            if not estado and not municipio:
                return None

            return {
                "estado": estado,
                "municipio": municipio,
                "colonias": sorted(set(colonias)) if colonias else [],
            }
        except Exception as exc:
            logger.error("Error parseando respuesta COPOMEX para CP %s: %s", cp, exc)
            return None

