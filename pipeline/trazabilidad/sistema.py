"""Sistema de trazabilidad del pipeline.

Modelo:

- `Run` es un context manager que agrupa una corrida del pipeline. Al entrar
  crea un directorio `runs/<timestamp>_<nombre>/` con dos archivos:
    - `log.txt`     -> logging humano (timestamp + nivel + mensaje).
    - `eventos.jsonl` -> eventos estructurados (uno por linea, JSON).
- `evento(nombre, **kw)` es una funcion libre que registra un evento en el
  Run activo, o lo descarta silenciosamente si no hay ninguno.
- `run_actual()` devuelve la Run activa actual (o None) usando ContextVar
  para soportar threads y asyncio.
- `Run.medir(nombre)` es un context manager que mide tiempo y deja un
  evento `medir` con la duracion en segundos.

Esta implementacion es deliberadamente minima y sin dependencias externas:
solo `logging`, `json`, `contextvars`, `pathlib`, `datetime` y `threading`.
"""

from __future__ import annotations

import contextlib
import contextvars
import json
import logging
import threading
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_run_actual: contextvars.ContextVar["Run | None"] = contextvars.ContextVar(
    "run_actual", default=None
)


def run_actual() -> "Run | None":
    """Devuelve la `Run` activa en el contexto actual, o None."""
    return _run_actual.get()


def _serializar(obj: Any) -> Any:
    if isinstance(obj, (datetime,)):
        return obj.isoformat()
    if isinstance(obj, Path):
        return str(obj)
    return str(obj)


class Run:
    """Context manager que representa una corrida del pipeline.

    Uso:
        with Run("zarr_no2", contexto={"fuente": "no2"}) as run:
            run.info("hola")
            with run.medir("paso_lento"):
                ...
            evento("archivo_procesado", path="x.tif")
    """

    def __init__(
        self,
        nombre: str,
        contexto: dict | None = None,
        root: str | Path = "runs",
    ) -> None:
        self.nombre = nombre
        self.contexto: dict[str, Any] = dict(contexto or {})
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        self.id = f"{ts}_{nombre}"
        self.dir = Path(root) / self.id
        self.eventos_path = self.dir / "eventos.jsonl"
        self.log_path = self.dir / "log.txt"
        self.t0: float | None = None
        self._token: contextvars.Token | None = None
        self._lock = threading.Lock()
        self._file_handler: logging.Handler | None = None
        self._stream_handler: logging.Handler | None = None
        self._logger = logging.getLogger(f"pipeline.run.{self.id}")
        self._logger.setLevel(logging.DEBUG)
        self._logger.propagate = False

    def __enter__(self) -> "Run":
        self.dir.mkdir(parents=True, exist_ok=True)
        self.t0 = time.monotonic()

        fh = logging.FileHandler(self.log_path, encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)-7s %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        self._logger.addHandler(fh)
        self._file_handler = fh

        sh = logging.StreamHandler()
        sh.setLevel(logging.INFO)
        sh.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)-7s %(message)s",
                datefmt="%H:%M:%S",
            )
        )
        self._logger.addHandler(sh)
        self._stream_handler = sh

        self._token = _run_actual.set(self)
        self._registrar(
            {
                "_evento": "run_inicio",
                "nombre": self.nombre,
                "contexto": self.contexto,
                "run_id": self.id,
                "log_path": str(self.log_path),
            }
        )
        self.info("=== run %s iniciado ===", self.id)
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        dt = time.monotonic() - (self.t0 or time.monotonic())
        excepcion: str | None = None
        if exc is not None:
            excepcion = "".join(traceback.format_exception_only(type(exc), exc)).strip()
            self.error("run termino con excepcion", exc, exc_info=True)
        self._registrar(
            {
                "_evento": "run_fin",
                "nombre": self.nombre,
                "duracion_s": round(dt, 3),
                "excepcion": excepcion,
            }
        )
        self.info("=== run %s fin (%.2fs) ===", self.id, dt)

        if self._file_handler is not None:
            self._logger.removeHandler(self._file_handler)
            try:
                self._file_handler.close()
            except Exception:
                pass
            self._file_handler = None
        if self._stream_handler is not None:
            self._logger.removeHandler(self._stream_handler)
            self._stream_handler = None
        if self._token is not None:
            try:
                _run_actual.reset(self._token)
            except Exception:
                _run_actual.set(None)
            self._token = None
        return False

    def _registrar(self, payload: dict) -> None:
        payload = {
            "_ts": datetime.now(timezone.utc).isoformat(),
            **payload,
        }
        with self._lock:
            self.dir.mkdir(parents=True, exist_ok=True)
            with self.eventos_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(payload, ensure_ascii=False, default=_serializar) + "\n")

    def evento(self, nombre: str, **kw: Any) -> None:
        """Registra un evento estructurado en `eventos.jsonl`."""
        self._registrar({"_evento": nombre, **kw})

    def info(self, msg: str, *args: Any) -> None:
        self._logger.info(msg, *args)

    def warning(self, msg: str, *args: Any) -> None:
        self._logger.warning(msg, *args)

    def debug(self, msg: str, *args: Any) -> None:
        self._logger.debug(msg, *args)

    def error(self, msg: str, exc: BaseException | None = None, exc_info: bool = False) -> None:
        if exc is None:
            self._logger.error(msg, exc_info=exc_info)
        elif exc_info:
            self._logger.error("%s :: %s", msg, exc, exc_info=True)
        else:
            self._logger.error("%s :: %s", msg, exc)

    @contextlib.contextmanager
    def medir(self, nombre: str):
        """Mide el tiempo de un bloque y emite un evento `medir`."""
        t = time.monotonic()
        self.info("[medir] inicio: %s", nombre)
        ok = True
        try:
            yield
        except BaseException:
            ok = False
            raise
        finally:
            dt = time.monotonic() - t
            self.info("[medir] fin:   %s (%.2fs, ok=%s)", nombre, dt, ok)
            self.evento("medir", tarea=nombre, duracion_s=round(dt, 3), ok=ok)


def evento(nombre: str, **kw: Any) -> None:
    """Registra un evento en el `Run` actual, si lo hay; si no, descarta."""
    r = run_actual()
    if r is not None:
        r.evento(nombre, **kw)
