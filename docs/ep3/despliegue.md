# Despliegue de la página de EP3

La página (Streamlit) corre **solo en su equipo**. No hornea datos en la imagen, no usa la red para nada que no sea instalar paquetes y no envía datos de Waymo a ningún servicio.

**Estado de las pruebas (2026-11-14):** local en Windows, probada con pruebas automáticas (`tests/ep3/test_app.py`, `streamlit.testing.v1.AppTest`, datos sintéticos). **Docker: no probado**: Docker 28.3.0 está instalado, pero el demonio (Docker Desktop) estaba apagado y no se encendió por iniciativa propia. **AWS: no ejecutado** (solo guía).

## 1. Qué necesita la página
- `data/09_app_ep3/`: tablas con predicciones fuera de fold (las crea `scripts/ep3/f7_preparar_app.py`).
- `data/06_models_ep3/`: la solución congelada v3 (la crea `scripts/ep3/f6_final.py`) y, opcional, `no_supervisado_v3.joblib` (la crea `scripts/ep3/f13_no_supervisado.py`; sin él la página no muestra el «tipo de caso»).
- Variables opcionales: `WAYMO_APP_DATA` y `WAYMO_APP_MODELOS` para cambiar las carpetas.

## 2. Local (Windows)
```
python -m venv .venv
.venv\Scripts\pip install -r requirements_app.txt -c constraints_ep3.txt
scripts\ep3\arrancar_app.bat          (o .\scripts\ep3\arrancar_app.ps1)
```
Se abre en http://localhost:8501 (solo accesible desde su equipo). Para detenerla: Ctrl+C. Desde la línea de comandos del repositorio con su entorno ya creado: `python -m streamlit run app/app.py`.

## 3. Docker (solo local)
```
docker compose up --build        (o .\scripts\ep3\arrancar_docker.ps1)
```
- `Dockerfile`: `python:3.10-slim`, instala `requirements_app.txt` con `-c constraints_ep3.txt`, usuario sin privilegios, `HEALTHCHECK`.
- `.dockerignore`: lista blanca; **`data/` y todo `*.parquet` o `*.joblib` quedan fuera** de la imagen. Entran `app/` y `src/waymo_evaluacion/ep3/`.
- `docker-compose.yml`: monta `data/09_app_ep3` y `data/06_models_ep3` como **volumen de solo lectura**; publica el puerto solo en el equipo (`"127.0.0.1:8501:8501"`). El `Dockerfile` deja `--server.address=0.0.0.0` porque dentro del contenedor es necesario; lo que limita el acceso es el compose.
- Comprobación recomendada tras construir: `docker run --rm waymo-ep3-app:local ls /app` no debe mostrar `data/` con contenido, y `docker history waymo-ep3-app:local` no debe tener capas de datos.
- Si el build falla en `xgboost` o `lightgbm`, falta `libgomp1` (el `Dockerfile` ya la instala).

## 4. Guía para AWS (EC2 + S3 privado) - NO ejecutada, solo orientativa
**Advertencia de licencia.** El Waymo Open Dataset es de uso no comercial y no se puede redistribuir; sus datos y lo derivado por caja (identificadores, puntajes por caja) **no deben subirse a un servicio externo** sin permiso de la licencia. Las tablas `cajas_oof.parquet` y los parquets de `lidar_box` son datos de ese tipo. Esta guía queda como material de estudio: antes de usarla, revise los términos vigentes de Waymo o use un paquete de datos agregado (celdas, Lista A, curva, KPIs), sin filas por caja. La página actual necesita las filas por caja en las secciones 3 y 4, así que **no se recomienda desplegarla en la nube tal como está**.

Si algún día se cumple la condición anterior, el esquema sería:
1. **S3 privado.** Crear un bucket con *Block Public Access* activo, cifrado SSE-S3 o SSE-KMS, versionado y registro de accesos. Subir solo el paquete permitido.
2. **IAM con mínimo privilegio.** Un rol de instancia (*instance profile*) con `s3:GetObject` solo sobre el prefijo del paquete. **Sin claves de acceso en archivos ni variables de entorno.**
3. **EC2 pequeña** (por ejemplo `t3.small`, Amazon Linux o Ubuntu) con Docker. El grupo de seguridad **no abre 8501 a internet**: solo SSH o SSM desde su IP.
4. **Acceso.** Túnel SSH o AWS SSM Session Manager hacia `localhost:8501`; o un *Application Load Balancer* con autenticación (Cognito) y HTTPS si hubiera que compartirla.
5. **Arranque.** `aws s3 sync` del paquete a `/srv/waymo/data`, `docker compose up -d` con los volúmenes de solo lectura apuntando a esa carpeta.
6. **Operación.** Apagar la instancia cuando no se use, etiquetar recursos, alarma de costo y borrar el bucket al terminar el curso.

## 5. Seguridad de la página
- **Escucha solo en `localhost`.** `.streamlit/config.toml` fija `server.address = "localhost"`, `headless = false`, `browser.gatherUsageStats = false` y `client.toolbarMode = "minimal"` (sin el botón Deploy). `scripts/ep3/arrancar_app.bat` (y `.ps1`) repiten `--server.address localhost` y `--browser.gatherUsageStats false`. Antes la página arrancaba en todas las interfaces y mostraba la *Network URL* y la *External URL*.
- **Nunca se debe exponer sin autenticación y sin quitar los identificadores** (la página muestra `laser_object_id` y marcas de tiempo en sus tablas y descargas).
- **No se publica en servicios de nube con datos de Waymo** (licencia de uso no comercial; ver la advertencia de la sección 4).
- En Docker: contenedor en `0.0.0.0`, pero el puerto se publica solo como `127.0.0.1:8501:8501`; `.dockerignore` deja `data/` fuera de la imagen.
- Una prueba de solo lectura, `tests/ep3/test_seguridad_pagina.py`, falla si `address` deja de ser `localhost`, si `toolbarMode` no es `minimal` o si el compose publica el puerto sin `127.0.0.1`.

## 6. Privacidad y límites
- La sección «Puntuar datos nuevos» procesa el archivo en memoria y no escribe nada.
- Telemetría desactivada (`browser.gatherUsageStats = false`).
