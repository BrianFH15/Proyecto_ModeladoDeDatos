from datetime import date
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError

from app.db import get_quotes_collection
from app.models import QuoteDocument, QuoteListResponse
from app.services.quotes import (
    create_quote,
    delete_quote,
    get_quote,
    list_quotes,
    replace_quote,
)

router = APIRouter(prefix="/api/v1/cotizaciones", tags=["cotizaciones"])
QuotesCollection = Annotated[
    Collection[dict[str, Any]],
    Depends(get_quotes_collection),
]


@router.post(
    "",
    response_model=QuoteDocument,
    status_code=status.HTTP_201_CREATED,
    summary="Crear cotización simulada",
)
def post_quote(
    quote: QuoteDocument,
    collection: QuotesCollection,
) -> dict[str, Any]:
    try:
        return create_quote(collection, quote)
    except DuplicateKeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una cotización con ese id_documento.",
        ) from exc


@router.get(
    "",
    response_model=QuoteListResponse,
    summary="Listar cotizaciones con paginación y filtros",
)
def get_quotes(
    collection: QuotesCollection,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    destino: Annotated[str | None, Query(min_length=2, max_length=100)] = None,
    check_in: date | None = None,
    adultos: Annotated[int | None, Query(ge=1, le=40)] = None,
) -> dict[str, Any]:
    items, total = list_quotes(
        collection,
        limit=limit,
        offset=offset,
        destino=destino,
        check_in=check_in,
        adultos=adultos,
    )
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.get(
    "/{document_id}",
    response_model=QuoteDocument,
    summary="Obtener cotización por id_documento",
)
def get_quote_by_id(
    document_id: UUID,
    collection: QuotesCollection,
) -> dict[str, Any]:
    quote = get_quote(collection, document_id)
    if quote is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró la cotización.",
        )
    return quote


@router.put(
    "/{document_id}",
    response_model=QuoteDocument,
    summary="Reemplazar cotización",
)
def put_quote(
    document_id: UUID,
    quote: QuoteDocument,
    collection: QuotesCollection,
) -> dict[str, Any]:
    if quote.metadata_extraccion.id_documento != document_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El id_documento del cuerpo debe coincidir con el de la ruta.",
        )
    try:
        if not replace_quote(collection, document_id, quote):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se encontró la cotización.",
            )
    except DuplicateKeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El reemplazo entra en conflicto con otra cotización.",
        ) from exc
    return quote.model_dump(mode="json")


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Eliminar cotización",
)
def remove_quote(
    document_id: UUID,
    collection: QuotesCollection,
) -> Response:
    if not delete_quote(collection, document_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró la cotización.",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
