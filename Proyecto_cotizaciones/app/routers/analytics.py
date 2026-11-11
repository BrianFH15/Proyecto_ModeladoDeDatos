from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, Query
from pymongo.collection import Collection

from app.db import get_quotes_collection
from app.models import (
    CheapestHotelOffer,
    DestinationRateSummary,
    MonthlyQuoteSummary,
)
from app.services.analytics import (
    average_rate_by_destination,
    cheapest_hotel_offers,
    quote_counts_by_month,
)

router = APIRouter(prefix="/api/v1/analytics", tags=["análisis"])
QuotesCollection = Annotated[
    Collection[dict[str, Any]],
    Depends(get_quotes_collection),
]


@router.get(
    "/tarifa-promedio-por-destino",
    response_model=list[DestinationRateSummary],
    summary="Tarifa promedio por destino",
)
def get_average_rate_by_destination(
    collection: QuotesCollection,
) -> list[dict[str, Any]]:
    return average_rate_by_destination(collection)


@router.get(
    "/hoteles-mas-economicos",
    response_model=list[CheapestHotelOffer],
    summary="Hoteles más económicos, opcionalmente por categoría",
)
def get_cheapest_hotels(
    collection: QuotesCollection,
    limit: Annotated[int, Query(ge=1, le=100)] = 5,
    destino: Annotated[str | None, Query(min_length=2, max_length=100)] = None,
    categoria: Annotated[
        Literal["SCC", "3EST", "4EST", "5EST", "BOU"] | None,
        Query(),
    ] = None,
) -> list[dict[str, Any]]:
    return cheapest_hotel_offers(
        collection,
        limit=limit,
        destino=destino,
        categoria=categoria,
    )


@router.get(
    "/cotizaciones-por-mes",
    response_model=list[MonthlyQuoteSummary],
    summary="Número de cotizaciones agrupadas por mes",
)
def get_quote_counts_by_month(
    collection: QuotesCollection,
) -> list[dict[str, Any]]:
    return quote_counts_by_month(collection)
