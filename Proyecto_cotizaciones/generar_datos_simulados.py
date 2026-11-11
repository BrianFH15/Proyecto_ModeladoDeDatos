import argparse
import json
import random
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
QUOTE_FILE = ROOT / "cotizaciones_hostech_simuladas.json"
DESTINATIONS = (
    "Riviera Maya - MX",
    "Cancún - MX",
    "Puerto Vallarta - MX",
    "Los Cabos - MX",
    "Oaxaca - MX",
    "Mérida - MX",
)
ROOM_TYPES = (
    "Doble Standard",
    "Doble Superior Dos Camas",
    "Habitación Familiar",
    "Suite Junior",
    "Habitación con Vista al Mar",
)
MEAL_PLANS = (
    "Sólo Habitación",
    "Desayuno Incluido",
    "Desayuno y Cena",
    "Todo Incluido",
)
CATEGORIES = ("SCC", "3EST", "4EST", "5EST", "BOU")
HOTELS_BY_DESTINATION = {
    "Riviera Maya - MX": (
        "Marea Serena Resort",
        "Casa Coral Boutique Hotel",
        "Arena Clara Suites",
        "Brisa del Manglar Hotel",
        "Costa Lucero Resort",
        "Mar de Ámbar Hotel",
        "Selva Azul Boutique Suites",
        "Piedra de Luna Resort",
    ),
    "Cancún - MX": (
        "Bahía Esmeralda Hotel",
        "Casa Nicté Suites",
        "Costa Dorada Resort",
        "Mar de Jade Boutique Hotel",
        "Brisas de Nichupté",
        "Arena Blanca Suites",
        "Punta Celeste Hotel",
        "Villa del Faro Resort",
    ),
    "Puerto Vallarta - MX": (
        "Bahía Serena Hotel",
        "Casa Miramar Boutique Suites",
        "Costa de Palma Resort",
        "Brisa del Pacífico Hotel",
        "Villa Marina Suites",
        "Punta Arena Resort",
        "Mar de Olivos Hotel",
        "Jardines de la Bahía",
    ),
    "Los Cabos - MX": (
        "Costa de Cobre Resort",
        "Casa del Desierto Hotel",
        "Mar de Cortés Suites",
        "Punta Cardón Resort",
        "Arena del Arco Hotel",
        "Brisa de Baja Boutique Suites",
        "Villa del Estero",
        "Bahía Dorada Hotel",
    ),
    "Oaxaca - MX": (
        "Casa del Laurel Hotel",
        "Patio de los Naranjos",
        "Hotel Canto de Barro",
        "Casa Nube Boutique Suites",
        "Posada del Andador",
        "Jardín de Mitla Hotel",
        "La Casona del Tule",
        "Casa de la Cantera",
    ),
    "Mérida - MX": (
        "Casa del Mayab Hotel",
        "Patio de Santa Lucía",
        "Hacienda Ceiba Suites",
        "Casa del Naranjo Boutique Hotel",
        "Paseo de las Palmas",
        "Hotel Casona de Itzá",
        "Casa del Aljibe",
        "Hacienda del Sol Mérida",
    ),
}


def simulated_uuid(kind: str, index: int) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"hostech-simulado-{kind}-{index}"))


def write_json(path: Path, documents: list[dict]) -> None:
    path.write_text(
        json.dumps(documents, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def generate_quotes(count: int, rng: random.Random) -> list[dict]:
    documents = []
    generated_at = datetime.now(timezone.utc).isoformat()
    today = date.today()

    for index in range(1, count + 1):
        destination = rng.choice(DESTINATIONS)
        nights = rng.randint(2, 7)
        check_in = today + timedelta(days=rng.randint(10, 180))
        check_out = check_in + timedelta(days=nights)
        room_count = rng.randint(1, 2)
        adults = rng.randint(1, 4) * room_count
        children = rng.randint(0, 2)
        hotel_count = rng.randint(5, 8)
        hotel_names = rng.sample(HOTELS_BY_DESTINATION[destination], hotel_count)
        hotels = []

        for hotel_index in range(1, hotel_count + 1):
            nightly_rate = round(rng.uniform(650, 6500), 2)
            room_options = []
            for room_index in range(rng.randint(1, 3)):
                room_total = round(
                    nightly_rate * nights * rng.uniform(0.9, 1.65), 2
                )
                cancellation_text = rng.choice(
                    (
                        "Tarifa no reembolsable.",
                        "Cancelación sin cargo hasta 7 días antes de la llegada.",
                        "Cargo de una noche por cancelación tardía.",
                    )
                )
                room_options.append(
                    {
                        "tipo_habitacion": rng.choice(ROOM_TYPES),
                        "plan_alimento": rng.choice(MEAL_PLANS),
                        "costo_total": room_total,
                        "moneda": "MXN",
                        "estado_disponibilidad": rng.choice(
                            ("confirmado", "sujeto a disponibilidad")
                        ),
                        "politicas": {
                            "fecha_limite_pago": (
                                check_in - timedelta(days=rng.randint(1, 14))
                            ).isoformat(),
                            "cargos_cancelacion": cancellation_text,
                            "cargos_no_show": (
                                f"Penalidad simulada de ${room_total:.2f} MXN."
                            ),
                        },
                    }
                )

            hotels.append(
                {
                    "hotel_nombre": hotel_names[hotel_index - 1],
                    "categoria": rng.choice(CATEGORIES),
                    "ubicacion": destination.split(" - ")[0],
                    "tarifa_promedio_noche": nightly_rate,
                    "costo_total_estancia": round(nightly_rate * nights, 2),
                    "moneda": "MXN",
                    "opciones_habitacion": room_options,
                }
            )

        documents.append(
            {
                "metadata_extraccion": {
                    "id_documento": simulated_uuid("cotizacion", index),
                    "timestamp": generated_at,
                    "proveedor": "Hostech (datos simulados)",
                    "tipo_dato": "SIMULADO_NO_REAL",
                    "es_simulado": True,
                },
                "parametros_busqueda": {
                    "destino": destination,
                    "nacionalidad": rng.choice(
                        ("México", "Estados Unidos", "Canadá", "Colombia")
                    ),
                    "fechas": {
                        "check_in": check_in.isoformat(),
                        "check_out": check_out.isoformat(),
                        "noches": nights,
                    },
                    "ocupacion": {
                        "habitaciones": room_count,
                        "adultos": adults,
                        "menores": children,
                    },
                    "total_hoteles_disponibles": rng.randint(120, 1600),
                },
                "resultados": hotels,
            }
        )

    return documents


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Genera cotizaciones JSON claramente marcadas como simuladas."
    )
    parser.add_argument(
        "--cotizaciones",
        type=int,
        default=30,
        help="Número de búsquedas de cotización (predeterminado: 30).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Semilla para reproducir los datos (predeterminado: 42).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.cotizaciones < 0:
        raise SystemExit("El conteo de cotizaciones no puede ser negativo.")

    rng = random.Random(args.seed)
    quotes = generate_quotes(args.cotizaciones, rng)
    write_json(QUOTE_FILE, quotes)
    print(f"Cotizaciones simuladas: {len(quotes)} -> {QUOTE_FILE}")
    print("Todos los documentos están marcados como SIMULADO_NO_REAL.")


if __name__ == "__main__":
    main()
