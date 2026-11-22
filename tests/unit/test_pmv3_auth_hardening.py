import pytest

from src.adapters.outbound.persistence.supabase_repository_adapter import (
    InMemoryUsuarioRepository,
    SupabaseUsuarioRepository,
)
from src.application.use_cases.procesar_expediente_uc import AutenticarFuncionarioUseCase
from src.infrastructure.config import JWTTokenGenerator
from src.infrastructure.container import DependencyContainer


def test_hash_password_verifica_correcta_incorrecta_y_formato_invalido():
    password_hash = JWTTokenGenerator.generar_hash_password("clave-demo-segura")

    assert JWTTokenGenerator.verificar_password("clave-demo-segura", password_hash) is True
    assert JWTTokenGenerator.verificar_password("clave-erronea", password_hash) is False
    assert JWTTokenGenerator.verificar_password("clave-demo-segura", "formato-invalido") is False


def test_login_rechaza_rol_solicitado_distinto_del_rol_operativo():
    repositorio = InMemoryUsuarioRepository("clave-demo-segura")
    caso_uso = AutenticarFuncionarioUseCase(repositorio, JWTTokenGenerator)

    with pytest.raises(PermissionError, match="rol solicitado no coincide"):
        caso_uso.autenticar(
            "evaluador@eltambo.gob.pe",
            "clave-demo-segura",
            "MESA_DE_PARTES",
        )

    resultado = caso_uso.autenticar("admin.ti@eltambo.gob.pe", "clave-demo-segura", "ADMIN_TI")
    assert resultado["rol"] == "ADMIN_TI"
    assert resultado["correo"] == "admin.ti@eltambo.gob.pe"


def test_produccion_exige_secretos_y_no_usuarios_demo(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("RENDER", raising=False)
    monkeypatch.setenv("JWT_SECRET_KEY", "secreto-de-pruebas-con-longitud-suficiente-123456")
    monkeypatch.setenv("SUPABASE_URL", "https://proyecto.example.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "clave-publica-de-pruebas")
    monkeypatch.setenv("SUPABASE_SECRET_KEY", "clave-servicio-de-pruebas")

    contenedor = DependencyContainer()
    assert isinstance(contenedor.usuario_repo, SupabaseUsuarioRepository)

    monkeypatch.setenv("JWT_SECRET_KEY", "corto")
    with pytest.raises(RuntimeError, match="al menos 32 caracteres"):
        DependencyContainer()
