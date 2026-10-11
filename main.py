import uvicorn
from fastapi import FastAPI
from Src.Api.PredictAPI.predictAI import router

app = FastAPI()
app.include_router(router)


def custom_openapi():
    from fastapi.openapi.utils import get_openapi

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

app.openapi = custom_openapi


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
