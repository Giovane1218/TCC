import sys
from pathlib import Path
from fastapi.openapi.utils import get_openapi

# ====Constantes de nivel de acesso====
ADMIN_LEVEL = 1
USER_LEVEL = 2


def custom_openapi(app):

    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
    )

    for component in schema.get("components", {}).get("schemas", {}).values():
        for prop in component.get("properties", {}).values():
            if prop.get("contentMediaType") == "application/octet-stream":
                del prop["contentMediaType"]
                prop["format"] = "binary"

            items = prop.get("items", {})
            if items.get("contentMediaType") == "application/octet-stream":
                del items["contentMediaType"]
                items["format"] = "binary"

    app.openapi_schema = schema

    return schema


def getRootDir():
    ROOT_DIR = Path(__file__).resolve().parents[2]

    if str(ROOT_DIR) not in sys.path:
        sys.path.insert(0, str(ROOT_DIR))
    return ROOT_DIR
