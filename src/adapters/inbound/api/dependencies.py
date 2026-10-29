from typing import Any

from fastapi import Request


def obtener_container(request: Request) -> Any:
    return request.app.state.container
