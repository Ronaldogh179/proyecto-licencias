from pathlib import Path

HTML = Path("src/adapters/inbound/web_ui/index.html").read_text(encoding="utf-8")


def test_pantalla_login_dedicada_con_identidad_y_sin_selector_rol():
    assert 'id="pantallaLogin"' in HTML
    assert 'id="appShell"' in HTML
    assert 'id="loginForm"' in HTML
    assert 'id="loginCorreo"' in HTML
    assert 'id="loginPass"' in HTML
    assert 'id="togglePassword"' in HTML
    assert 'id="btnLogin"' in HTML
    assert 'id="btnLogout"' in HTML
    assert 'id="loginRol"' not in HTML
    assert 'name="rol"' not in HTML
    assert "Iniciar sesión" in HTML
    assert "PMV1-1-HU01 · Autenticación y control de acceso" in HTML
    assert "SIMEL" in HTML
    assert "Municipalidad Distrital de El Tambo" in HTML


def test_login_envia_solo_correo_y_password_y_muestra_errores_claros():
    assert "correo: document.getElementById('loginCorreo').value.trim()" in HTML
    assert "password: document.getElementById('loginPass').value" in HTML
    assert "rol:" not in HTML
    assert "Ingresa tu correo institucional." in HTML
    assert "Ingresa un correo institucional válido." in HTML
    assert "Ingresa tu contraseña." in HTML
    assert "Credenciales incorrectas. Verifica tu correo y contraseña." in HTML
    assert "Tu cuenta no tiene permisos para acceder a SIMEL." in HTML
    assert "El servicio de autenticación no está disponible" in HTML
    assert "No se pudo conectar con SIMEL. Verifica tu conexión" in HTML


def test_sesion_guarda_usuario_rol_y_permite_cerrar_sesion():
    assert "const SIMEL_USER_KEY = 'simel_usuario';" in HTML
    assert "const SIMEL_ROLE_KEY = 'simel_rol';" in HTML
    assert "function guardarSesion(data)" in HTML
    assert "function mostrarApp()" in HTML
    assert "function cerrarSesion(" in HTML
    assert "sessionStorage.setItem(SIMEL_USER_KEY" in HTML
    assert "sessionStorage.setItem(SIMEL_ROLE_KEY" in HTML
    assert "document.getElementById('btnLogout')?.addEventListener('click', () => cerrarSesion());" in HTML
    assert "nombreEl.innerText = nombre" in HTML
    assert "rolEl.innerText = 'Rol: '" in HTML


def test_sesion_vencida_muestra_login_y_permite_reingreso():
    assert "function decodificarPayloadJwt(token)" in HTML
    assert "function tokenEstaVencido(token)" in HTML
    assert "function manejarSesionExpirada(" in HTML
    assert "function mostrarLogin(" in HTML
    assert "Tu sesión venció. Ingresa nuevamente para continuar." in HTML
    assert "response.status === 401 && !url.includes('/auth/login')" in HTML
    assert "window.fetch = async (input, init)" in HTML
    assert "if (!tokenGuardado) mostrarLogin();" in HTML


def test_password_se_puede_mostrar_u_ocultar_y_no_se_expone_token():
    assert "input.type = mostrar ? 'text' : 'password';" in HTML
    assert "pass.type = 'password';" in HTML
    assert "texto.innerText = mostrar ? 'Ocultar' : 'Mostrar';" in HTML
    assert 'aria-label="Mostrar contraseña"' in HTML
    assert "TOKEN JWT EMITIDO" not in HTML
    assert 'id="tokenBox"' not in HTML
