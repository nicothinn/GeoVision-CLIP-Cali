"""Plugin/hook para reenviar logs de workers Dask al stdout del cliente.

`forward_logs(client)` configura cada worker para que su `logging` root
emita a stdout en un formato unificado. Esto permite ver en una sola
terminal los mensajes de todos los workers, sin tener que abrir el
dashboard.

La implementacion es defensiva: si `register_worker_callbacks` no esta
disponible o falla, se intenta `client.run(...)` como fallback y, si todo
falla, se loguea un warning pero NO se levanta para no romper el pipeline.
"""

from __future__ import annotations

import logging
import sys


def _configurar_worker_logging() -> None:  # pragma: no cover - corre en worker
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    for h in list(root.handlers):
        try:
            root.removeHandler(h)
        except Exception:
            pass
    sh = logging.StreamHandler(stream=sys.stdout)
    sh.setLevel(logging.INFO)
    sh.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)-7s [worker] %(message)s",
            datefmt="%H:%M:%S",
        )
    )
    root.addHandler(sh)
    logging.getLogger("distributed").setLevel(logging.WARNING)
    logging.getLogger("distributed.worker").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("googleapiclient").setLevel(logging.WARNING)
    logging.getLogger("google").setLevel(logging.WARNING)


def forward_logs(client) -> None:
    """Hace que cada worker emita su logging root a stdout."""
    log = logging.getLogger("pipeline.trazabilidad.dask")
    intentos: list[tuple[str, Exception]] = []
    try:
        client.register_worker_callbacks(setup=_configurar_worker_logging)
        return
    except Exception as e:  # pragma: no cover - depende del cluster
        intentos.append(("register_worker_callbacks", e))

    try:
        client.run(_configurar_worker_logging)
        return
    except Exception as e:  # pragma: no cover
        intentos.append(("client.run", e))

    for nombre, exc in intentos:
        log.warning("forward_logs: %s fallo (%s)", nombre, exc)
