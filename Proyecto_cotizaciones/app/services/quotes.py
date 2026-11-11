from datetime import date
from typing import Any
from uuid import UUID

from pymongo.collection import Collection

from app.db import NATURAL_KEY_PATH
from app.models import QuoteDocument


def create_quote(
    collection: Collection[dict[str, Any]],
    quote: QuoteDocument,
) -> dict[str, Any]:
    document = quote.model_dump(mode="json")
    collection.insert_one(document)
    document.pop("_id", None)
    return document


def list_quotes(
    collection: Collection[dict[str, Any]],
    *,
    limit: int,
    offset: int,
    destino: str | None,
    check_in: date | None,
    adultos: int | None,
) -> tuple[list[dict[str, Any]], int]:
    filters: dict[str, Any] = {"metadata_extraccion.es_simulado": True}
    if destino is not None:
        filters["parametros_busqueda.destino"] = destino
    if check_in is not None:
        filters["parametros_busqueda.fechas.check_in"] = check_in.isoformat()
    if adultos is not None:
        filters["parametros_busqueda.ocupacion.adultos"] = adultos

    total = collection.count_documents(filters)
    cursor = (
        collection.find(filters, {"_id": False})
        .sort(NATURAL_KEY_PATH, 1)
        .skip(offset)
        .limit(limit)
    )
    return [document for document in cursor], total


def get_quote(
    collection: Collection[dict[str, Any]],
    document_id: UUID,
) -> dict[str, Any] | None:
    document = collection.find_one(
        {NATURAL_KEY_PATH: str(document_id)},
        {"_id": False},
    )
    return document


def replace_quote(
    collection: Collection[dict[str, Any]],
    document_id: UUID,
    quote: QuoteDocument,
) -> bool:
    result = collection.replace_one(
        {NATURAL_KEY_PATH: str(document_id)},
        quote.model_dump(mode="json"),
        upsert=False,
    )
    return result.matched_count == 1


def delete_quote(
    collection: Collection[dict[str, Any]],
    document_id: UUID,
) -> bool:
    result = collection.delete_one({NATURAL_KEY_PATH: str(document_id)})
    return result.deleted_count == 1
