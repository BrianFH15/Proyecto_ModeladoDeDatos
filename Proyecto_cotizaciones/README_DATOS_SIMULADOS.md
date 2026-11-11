# Datos simulados para MongoDB

El archivo de esta carpeta contiene cotizaciones de prueba claramente
separadas de cualquier dato transcrito o real:

- `cotizaciones_hostech_simuladas.json`: cotizaciones y hoteles ficticios.

Todos los documentos están marcados con `es_simulado: true` y
`tipo_dato: "SIMULADO_NO_REAL"`. Los hoteles, precios, disponibilidad y
políticas son ficticios; no representan ofertas reales de Hostech. El conjunto
no incluye promociones ni URLs de hoteles o imágenes.

## Regenerar los datos

El generador utiliza solo la biblioteca estándar de Python:

```powershell
python .\generar_datos_simulados.py --cotizaciones 30 --seed 42
```

Puedes cambiar las cantidades y la semilla. Una misma semilla reproduce los
mismos datos, salvo la marca de tiempo de generación.

## Importar a MongoDB

Importa la colección simulada:

```powershell
mongoimport --db TU_DB --collection cotizaciones_hostech_simuladas --file ".\cotizaciones_hostech_simuladas.json" --jsonArray
```
