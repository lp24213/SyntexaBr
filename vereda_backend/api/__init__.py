from fastapi import FastAPI

from vereda_backend.api import routes


def include_api_routes(app: FastAPI) -> None:
    routes.register(app)

