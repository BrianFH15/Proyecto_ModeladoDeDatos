from datetime import date, datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ExtractionMetadata(ApiModel):
    id_documento: UUID
    timestamp: datetime
    proveedor: Literal["Hostech (datos simulados)"]
    tipo_dato: Literal["SIMULADO_NO_REAL"]
    es_simulado: Literal[True]


class StayDates(ApiModel):
    check_in: date
    check_out: date
    noches: Annotated[int, Field(ge=1, le=90)]

    @model_validator(mode="after")
    def validate_night_count(self) -> "StayDates":
        if self.check_out <= self.check_in:
            raise ValueError("check_out debe ser posterior a check_in.")
        if (self.check_out - self.check_in).days != self.noches:
            raise ValueError("noches debe coincidir con la diferencia entre fechas.")
        return self


class Occupancy(ApiModel):
    habitaciones: Annotated[int, Field(ge=1, le=20)]
    adultos: Annotated[int, Field(ge=1, le=40)]
    menores: Annotated[int, Field(ge=0, le=40)]


class SearchParameters(ApiModel):
    destino: Annotated[str, Field(min_length=2, max_length=100)]
    nacionalidad: Annotated[str, Field(min_length=2, max_length=80)]
    fechas: StayDates
    ocupacion: Occupancy
    total_hoteles_disponibles: Annotated[int, Field(ge=0)]


class CancellationPolicies(ApiModel):
    fecha_limite_pago: date
    cargos_cancelacion: Annotated[str, Field(min_length=1, max_length=500)]
    cargos_no_show: Annotated[str, Field(min_length=1, max_length=500)]


class RoomOption(ApiModel):
    tipo_habitacion: Annotated[str, Field(min_length=1, max_length=120)]
    plan_alimento: Annotated[str, Field(min_length=1, max_length=100)]
    costo_total: Annotated[float, Field(ge=0, allow_inf_nan=False)]
    moneda: Annotated[str, Field(min_length=3, max_length=3)]
    estado_disponibilidad: Literal["confirmado", "sujeto a disponibilidad"]
    politicas: CancellationPolicies


class HotelResult(ApiModel):
    hotel_nombre: Annotated[str, Field(min_length=1, max_length=160)]
    categoria: Annotated[str, Field(min_length=1, max_length=20)]
    ubicacion: Annotated[str, Field(min_length=1, max_length=100)]
    tarifa_promedio_noche: Annotated[float, Field(ge=0, allow_inf_nan=False)]
    costo_total_estancia: Annotated[float, Field(ge=0, allow_inf_nan=False)]
    moneda: Annotated[str, Field(min_length=3, max_length=3)]
    opciones_habitacion: Annotated[list[RoomOption], Field(min_length=1)]


class QuoteDocument(ApiModel):
    metadata_extraccion: ExtractionMetadata
    parametros_busqueda: SearchParameters
    resultados: Annotated[list[HotelResult], Field(min_length=1)]


class QuoteListResponse(ApiModel):
    items: list[QuoteDocument]
    total: int
    limit: int
    offset: int


class DestinationRateSummary(ApiModel):
    destino: str
    tarifa_promedio_noche: float
    total_hoteles: int


class CheapestHotelOffer(ApiModel):
    id_documento: UUID
    destino: str
    check_in: date
    check_out: date
    hotel_nombre: str
    categoria: str
    ubicacion: str
    tarifa_promedio_noche: float
    costo_total_estancia: float
    moneda: str


class MonthlyQuoteSummary(ApiModel):
    mes: str
    total_cotizaciones: int
