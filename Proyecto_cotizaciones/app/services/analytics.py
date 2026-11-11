from typing import Any

from pymongo.collection import Collection


def average_rate_by_destination(
    collection: Collection[dict[str, Any]],
) -> list[dict[str, Any]]:
    pipeline = [
        {"$match": {"metadata_extraccion.es_simulado": True}},
        {"$unwind": "$resultados"},
        {
            "$group": {
                "_id": "$parametros_busqueda.destino",
                "tarifa_promedio_noche": {
                    "$avg": "$resultados.tarifa_promedio_noche"
                },
                "total_hoteles": {"$sum": 1},
            }
        },
        {
            "$project": {
                "_id": 0,
                "destino": "$_id",
                "tarifa_promedio_noche": 1,
                "total_hoteles": 1,
            }
        },
        {"$sort": {"destino": 1}},
    ]
    return list(collection.aggregate(pipeline))


def cheapest_hotel_offers(
    collection: Collection[dict[str, Any]],
    *,
    limit: int,
    destino: str | None,
    categoria: str | None,
) -> list[dict[str, Any]]:
    match: dict[str, Any] = {"metadata_extraccion.es_simulado": True}
    if destino is not None:
        match["parametros_busqueda.destino"] = destino
    if categoria is not None:
        match["resultados.categoria"] = categoria

    pipeline: list[dict[str, Any]] = [
        {"$match": match},
        {"$unwind": "$resultados"},
    ]
    if categoria is not None:
        pipeline.append({"$match": {"resultados.categoria": categoria}})
    pipeline.extend(
        [
            {
                "$sort": {
                    "resultados.tarifa_promedio_noche": 1,
                    "resultados.hotel_nombre": 1,
                }
            },
            {"$limit": limit},
            {
                "$project": {
                    "_id": 0,
                    "id_documento": "$metadata_extraccion.id_documento",
                    "destino": "$parametros_busqueda.destino",
                    "check_in": "$parametros_busqueda.fechas.check_in",
                    "check_out": "$parametros_busqueda.fechas.check_out",
                    "hotel_nombre": "$resultados.hotel_nombre",
                    "categoria": "$resultados.categoria",
                    "ubicacion": "$resultados.ubicacion",
                    "tarifa_promedio_noche": "$resultados.tarifa_promedio_noche",
                    "costo_total_estancia": "$resultados.costo_total_estancia",
                    "moneda": "$resultados.moneda",
                }
            },
        ]
    )
    return list(collection.aggregate(pipeline))


def quote_counts_by_month(
    collection: Collection[dict[str, Any]],
) -> list[dict[str, Any]]:
    pipeline = [
        {"$match": {"metadata_extraccion.es_simulado": True}},
        {
            "$match": {
                "metadata_extraccion.timestamp": {
                    "$type": "string",
                    "$regex": r"^\d{4}-\d{2}-",
                }
            }
        },
        {
            "$group": {
                "_id": {
                    "$substr": ["$metadata_extraccion.timestamp", 0, 7]
                },
                "total_cotizaciones": {"$sum": 1},
            }
        },
        {
            "$project": {
                "_id": 0,
                "mes": "$_id",
                "total_cotizaciones": 1,
            }
        },
        {"$sort": {"mes": 1}},
    ]
    return list(collection.aggregate(pipeline))
