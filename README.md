# hotdog-products-service

Servicio del menú de **PerroCaliente Express**: el CRUD de productos.

Python 3.12, FastAPI, SQLAlchemy, PostgreSQL.
Documentación general: [hotdog-docs](https://github.com/SeguridadInfromacion/hotdog-docs).

## API

| Método | Ruta | Quién | Qué hace |
|---|---|---|---|
| GET | `/api/products` | con sesión | Lista el menú (`?only_available=true` oculta los agotados) |
| GET | `/api/products/{id}` | con sesión | Un producto |
| POST | `/api/products` | admin | Crea un producto |
| PUT | `/api/products/{id}` | admin | Reemplaza un producto |
| DELETE | `/api/products/{id}` | admin | Elimina un producto |
| GET | `/api/products/audit` | admin | Bitácora de este servicio |

## Decisiones de seguridad

- **Solo verifica tokens.** Tiene la llave pública, no la privada: aunque este
  servicio fuera comprometido, no podría fabricar identidades.
- **Confianza cero.** Verifica firma, vencimiento, emisor y audiencia en cada
  petición, venga del gateway o de otro servicio.
- **Rol verificado en el servidor** en cada ruta que modifica datos.
- **Entradas estrictas.** Tipos, longitudes y rangos validados; campos
  desconocidos rechazados; ids aceptados solo como UUID.
- **Sin inyección SQL.** Todas las consultas pasan por el ORM con parámetros.
- **Auditoría** de cada alta, cambio y baja, con usuario e IP.

## Estructura

```
app/
  main.py          arranque, manejo de errores
  routes.py        HTTP -> casos de uso
  services.py      casos de uso
  repositories.py  acceso a datos
  models.py        tablas
  schemas.py       contratos de entrada y salida
  security.py      verificación de tokens
  dependencies.py  sesión, usuario actual, roles, anti-CSRF
  config.py        variables de entorno
tests/
```

## Desarrollo

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

pytest              # pruebas (SQLite en memoria, no necesitan Docker)
ruff check .
bandit -r app
pip-audit -r requirements.txt
```

Para ejecutarlo junto al resto del sistema, usa
[hotdog-infra](https://github.com/SeguridadInfromacion/hotdog-infra).

## Variables de entorno

| Variable | Obligatoria | Descripción |
|---|---|---|
| `DATABASE_URL` | sí | Conexión a PostgreSQL |
| `JWT_PUBLIC_KEY_FILE` | sí | Ruta a la llave pública RSA (PEM) |
| `ENABLE_DOCS` | no (false) | Activa `/docs` (solo para desarrollo) |
