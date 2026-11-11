from typing import Any

from fastapi import Request
from pymongo.collection import Collection

COLLECTION_NAME = "Proyecto"
NATURAL_KEY_PATH = "metadata_extraccion.id_documento"
NATURAL_KEY_INDEX = "uq_cotizacion_id_documento"


def get_quotes_collection(request: Request) -> Collection[dict[str, Any]]:
    return request.app.state.quotes_collection


def ensure_indexes(collection: Collection[dict[str, Any]]) -> None:
    collection.create_index(
        NATURAL_KEY_PATH,
        unique=True,
        name=NATURAL_KEY_INDEX,
    )
    collection.create_index(
        "parametros_busqueda.destino",
        name="ix_cotizacion_destino",
    )
