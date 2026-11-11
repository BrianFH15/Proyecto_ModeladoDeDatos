# Hostech Quotes API

API REST con FastAPI para administrar la colección `Proyecto` en la base
`Proyecto` de MongoDB Atlas. La colección contiene cotizaciones simuladas; los
documentos representan datos sintéticos y deben conservar `es_simulado: true`;
no son cotizaciones, precios ni disponibilidad reales.

La llave natural es `metadata_extraccion.id_documento`, un UUID. Al iniciar, la
API crea un índice único en ese campo y un índice por destino. MongoDB rechaza
duplicados incluso si dos solicitudes concurrentes intentan crear el mismo ID.

## Requisitos

- Python 3.11 o posterior
- `uv`
- Una base MongoDB Atlas y un usuario de base de datos con privilegio
  `readWrite` únicamente sobre esa base

## Instalación y configuración

Desde esta carpeta, en PowerShell:

```powershell
uv sync --extra dev
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Edita `.env` en tu equipo:

- `MONGO_URI`: URI de Atlas con un usuario de privilegios mínimos.
- `MONGO_DATABASE`: nombre exacto de la base (`Proyecto` es el valor de ejemplo
  usado por este proyecto).
- `CORS_ORIGINS`: orígenes de frontend separados por coma. El valor inicial
  permite `localhost:3000` y `localhost:5173`; no se admite `*`.

No compartas ni subas `.env`. `.env.example` solo contiene valores de ejemplo.
Si aún no importaste los datos, genera e importa el conjunto simulado:

```powershell
uv run python .\generar_datos_simulados.py --cotizaciones 100 --seed 42
$line = Get-Content .env | Where-Object { $_.StartsWith("MONGO_URI=") } | Select-Object -First 1
$env:MONGO_URI = $line.Substring("MONGO_URI=".Length)
mongoimport --uri "$env:MONGO_URI" --db Proyecto --collection Proyecto --file ".\cotizaciones_hostech_simuladas.json" --jsonArray
Remove-Item Env:MONGO_URI
```

Ese ejemplo carga temporalmente la URI desde `.env` para el proceso de
`mongoimport` y luego la quita del entorno de PowerShell.
La API no crea la base ni carga los JSON; solo crea los índices requeridos en la
colección `Proyecto`. Si ya hay documentos duplicados por
`metadata_extraccion.id_documento`, resuélvelos antes de iniciar la API.

## Ejecutar

```powershell
uv run uvicorn app.main:app --reload
```

Documentación interactiva: `http://127.0.0.1:8000/docs`.

## Endpoints

Base: `http://127.0.0.1:8000`. Los endpoints CRUD usan
`/api/v1/cotizaciones`; el identificador de ruta es `id_documento`.

| Método | Ruta | Resultado |
|---|---|---|
| GET | `/health` | Comprueba la conexión a MongoDB; 503 si no está disponible. |
| POST | `/api/v1/cotizaciones` | Crea una cotización; 201, 409 si el ID ya existe, 422 si es inválida. |
| GET | `/api/v1/cotizaciones` | Lista con `limit` (1–100), `offset` y filtros exactos `destino`, `check_in`, `adultos`. |
| GET | `/api/v1/cotizaciones/{id_documento}` | Obtiene una cotización; 404 si no existe. |
| PUT | `/api/v1/cotizaciones/{id_documento}` | Reemplaza el documento completo; el ID del cuerpo debe coincidir con la ruta. |
| DELETE | `/api/v1/cotizaciones/{id_documento}` | Elimina una cotización; 204 si se borró. |
| GET | `/api/v1/analytics/tarifa-promedio-por-destino` | Promedio de tarifas por noche y número de hoteles evaluados por destino. |
| GET | `/api/v1/analytics/hoteles-mas-economicos` | Top de hoteles por tarifa; admite `limit`, `destino` y `categoria` (`SCC`, `3EST`, `4EST`, `5EST`, `BOU`). |
| GET | `/api/v1/analytics/cotizaciones-por-mes` | Cuenta documentos por mes de extracción. |

Ejemplos de lectura:

```text
GET /health
GET /api/v1/cotizaciones?limit=10&offset=0&destino=Riviera%20Maya%20-%20MX
GET /api/v1/cotizaciones/00000000-0000-5000-8000-000000000001
GET /api/v1/analytics/tarifa-promedio-por-destino
GET /api/v1/analytics/hoteles-mas-economicos?limit=5&categoria=5EST&destino=Riviera%20Maya%20-%20MX
GET /api/v1/analytics/cotizaciones-por-mes
```

Ejemplo mínimo completo para crear (ajusta el UUID si vas a repetirlo):

```json
{
  "metadata_extraccion": {
    "id_documento": "c1aa41ce-58e0-4b79-9a9d-cd59ea09ecc4",
    "timestamp": "2026-11-09T12:00:00Z",
    "proveedor": "Hostech (datos simulados)",
    "tipo_dato": "SIMULADO_NO_REAL",
    "es_simulado": true
  },
  "parametros_busqueda": {
    "destino": "Riviera Maya - MX",
    "nacionalidad": "México",
    "fechas": {
      "check_in": "2026-12-12",
      "check_out": "2026-12-14",
      "noches": 2
    },
    "ocupacion": {
      "habitaciones": 1,
      "adultos": 2,
      "menores": 0
    },
    "total_hoteles_disponibles": 200
  },
  "resultados": [
    {
      "hotel_nombre": "Casa Coral Boutique Hotel",
      "categoria": "5EST",
      "ubicacion": "Riviera Maya",
      "tarifa_promedio_noche": 1500.0,
      "costo_total_estancia": 3000.0,
      "moneda": "MXN",
      "opciones_habitacion": [
        {
          "tipo_habitacion": "Doble Standard",
          "plan_alimento": "Sólo Habitación",
          "costo_total": 3000.0,
          "moneda": "MXN",
          "estado_disponibilidad": "confirmado",
          "politicas": {
            "fecha_limite_pago": "2026-12-01",
            "cargos_cancelacion": "Tarifa no reembolsable.",
            "cargos_no_show": "Penalidad simulada."
          }
        }
      ]
    }
  ]
}
```

Ejemplo PowerShell con `curl.exe`:

```powershell
curl.exe -X POST http://127.0.0.1:8000/api/v1/cotizaciones `
  -H "Content-Type: application/json" `
  --data-binary "@cotizacion.json"
curl.exe -X PUT http://127.0.0.1:8000/api/v1/cotizaciones/c1aa41ce-58e0-4b79-9a9d-cd59ea09ecc4 `
  -H "Content-Type: application/json" `
  --data-binary "@cotizacion.json"
curl.exe -X DELETE http://127.0.0.1:8000/api/v1/cotizaciones/c1aa41ce-58e0-4b79-9a9d-cd59ea09ecc4
```

Los endpoints de análisis usan aggregation pipelines de MongoDB. El filtro
`categoria=5EST` selecciona la categoría simulada de cinco estrellas y ordena
los resultados por menor `tarifa_promedio_noche`; es una categoría de prueba,
no una clasificación real verificada.

## Pruebas

Las pruebas usan MongoDB en memoria mediante `mongomock`; no requieren Atlas:

```powershell
uv run --extra dev pytest
```

Cubren `/health`, validación, alta, duplicados, paginación y filtros, búsqueda
por llave natural, reemplazo, borrado y los tres endpoints de análisis.

## Seguridad y checklist antes de Git

- `MONGO_URI` se carga desde `.env`; nunca se registra ni se devuelve al cliente.
- CORS usa orígenes configurables y rechaza el comodín `*`.
- Los filtros se construyen como documentos MongoDB con valores validados; no
  se aceptan nombres de campos ni fragmentos de consulta del usuario.
- Verifica que `.gitignore` excluya `.env` y que `.env.example` sí pueda
  versionarse.
- Antes de subir cambios, ejecuta `git status` y confirma que `.env` no aparezca.
- Si una URI o contraseña real se subió alguna vez, rótala en Atlas.
