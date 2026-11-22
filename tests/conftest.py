import os
import tempfile
from pathlib import Path

_DIRECTORIO_AISLADO = Path(tempfile.mkdtemp(prefix="simel_pytest_"))

os.environ.setdefault(
    "SIMEL_DB_PATH",
    str(_DIRECTORIO_AISLADO / "bd_expedientes_local.json"),
)
os.environ.setdefault(
    "JWT_SECRET_KEY",
    "simel-pytest-secret-solo-pruebas-2026",
)
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("SIMEL_DEMO_PASSWORD", "municipal2026")
os.environ["SUPABASE_URL"] = ""
os.environ["SUPABASE_KEY"] = ""
os.environ["SUPABASE_SECRET_KEY"] = ""
os.environ.pop("RENDER", None)
