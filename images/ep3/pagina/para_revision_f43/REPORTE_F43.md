# REPORTE F43: Lente listo para desplegar en EC2 (sin tocar AWS)

Escrito para: Rafa, que sube el paquete a la instancia y aprueba los textos del modo publicado. No se creó nada en AWS, no se activó el modo publicado y no hay commit.

## Avisos arriba (decisiones que no se pudieron cumplir tal cual)
1. **`cajas_oof.parquet` SÍ viaja.** El prompt decía que no viajara «si la app no lo necesita para arrancar»: lo necesita (`app/precarga.py` lo carga al arrancar y lo usan Resumen, Cola y Explica). Sin él la página no abre. Es 9,5 MB, 80.571 filas con identificadores de objeto, marcas de tiempo y geometría por caja, derivadas de `lidar_box` (no es el archivo crudo: el empaquetador comprueba que no traiga columnas de un `lidar_box` crudo). **La licencia de Waymo es no comercial y sin redistribución, y decidir si estos datos derivados pueden estar en un servidor sigue pendiente (DEC-150).** Si la respuesta es no, hay que cambiar la página para que arranque sin esas cajas, no solo quitar el archivo.
2. **El `.pem` y la IP:** la guía supone Amazon Linux 2023 (usuario `ec2-user`); con Ubuntu cambian solo la instalación de Docker y el usuario (`ubuntu`). Nada de esto se probó en AWS.
3. **No se pudo comprobar `--server.address 0.0.0.0` en esta máquina** (el entorno no permitió abrir el puerto a la red). La imagen sí corre en el contenedor con 0.0.0.0 (es el comando del Dockerfile) y se verificó por `127.0.0.1:8551`; el camino sin Docker se verificó con `localhost`.

## 1. Datos mínimos (medidos con el código, no a ojo)
Se instaló un gancho de auditoría de `open` (`sys.addaudithook`) en el proceso de la página real y se recorrieron sus 8 páginas y se puntuaron los 2 segmentos. Lo que abre:

| Ruta | Tamaño | Para qué |
|---|---|---|
| `data/09_app_ep3/cajas_oof.parquet` | 9,5 MB | cajas con puntaje fuera de fold (Resumen, Cola, Explica); lo carga la precarga |
| `data/09_app_ep3/` (`celdas.csv`, `clusters.csv`, `curva_cola.csv`, `kpis.json`, `lista_A.csv`) | 47 KB | tablas de las páginas |
| `data/09_app_ep3/evidencia/` (26 CSV) | 44 KB | pestañas de Validación |
| `data/06_models_ep3/modelo_final_v3.joblib`, `no_supervisado_v3.joblib` | 1,9 MB (el modelo final pesa 1,8 KB; los tipos de caso, 1,9 MB) | solución congelada y tipos de caso |
| `data/06_models_ep3/detector_params_v3.json`, `manifest_v3.json`, `umbrales_v3.json` | 2,3 KB | parámetros del detector |
| `docs/ep3/plan_v3.json` | 4 KB | umbrales que muestra Validación |

No se abren (y no viajan): `alternativas_v3.joblib`, `manifest_alternativas.json`, `manifest_no_supervisado.json`, el resto de `data/`, `datos_demo/` ni los zips. Escrituras durante todo el recorrido: solo directorios temporales de Python en el arranque, antes de cualquier subida; durante «Puntuar segmento» no se abrió ningún archivo para escribir, y `docker diff` del contenedor tras puntuar solo muestra el punto de montaje de `/app/data`.

Contenido de `despliegue_lente.zip` (167 archivos, **8,80 MB**, sha256 del archivo que quedó en la raíz `7a6d4aa1a6bdb169eabbbe11cc3e5ebbcd20a666143d6410ab41f3cc750e0f6d`): `app/` (17), `src/waymo_evaluacion/__init__.py` y `ep3/` (23), `artefactos_ep3/` (81), `.streamlit/`, `Dockerfile`, `.dockerignore`, `docker-compose.yml`, `requirements_app.txt`, `constraints_ep3.txt`, `docs/despliegue.json`, `docs/ep3/plan_v3.json`, los datos de la tabla, y un `LEEME_DESPLIEGUE.txt` con los comandos. (`conf/` no hace falta: la página no usa Kedro.) Regenerarlo: `.venv\Scripts\python scripts/ep3/empaquetar_despliegue.py`. El hash del zip cambia en cada armado aunque el contenido sea idéntico (el zip guarda fechas); se comprobó que el archivo final tiene los mismos 167 miembros, byte a byte, que el desempaquetado con que se construyó y probó la imagen.

## 2. Paquete
`scripts/ep3/empaquetar_despliegue.py`: lista blanca explícita; **falla sin escribir el zip** si encuentra parquet crudo (`lidar_box*`, `camera_to_lidar_box_association*`), `datos_demo/`, `.venv`, `.git`, `notebooks/`, `tests/`, `images/`, zips, llaves `.pem`, `.env`, cualquier archivo de `data/` fuera de la lista, un parquet que no sea `cajas_oof.parquet` o un `cajas_oof.parquet` con columnas de un `lidar_box` crudo. Imprime contenido, tamaño y sha256. `.gitignore` agrega `despliegue_lente.zip` (no estaba cubierto).

## 3. Contenedor
- `Dockerfile`: ya escuchaba en `0.0.0.0:8501`, con `STREAMLIT_BROWSER_GATHER_USAGE_STATS=false`, sin datos en la imagen (solo `app/`, `src/waymo_evaluacion/ep3`, `.streamlit` de `app/`), usuario sin privilegios (`app`) y healthcheck. `docker-compose.yml` sigue publicando solo en `127.0.0.1` (lo vigila `test_seguridad_pagina.py`); para EC2 se usa `docker run`.
- `server.maxUploadSize = 500` (MB) en las dos `config.toml`; el `lidar_box` más grande de la demostración pesa 1,73 MB.
- **Se construyó y corrió con Docker** (28.3.0; el motor estaba apagado y se inició Docker Desktop): imagen `lente:f43` construida desde el zip desempaquetado en una carpeta temporal (**2,17 GB**; en EC2 conviene un disco de 16 a 20 GB). Contenedor sin política de reinicio, `127.0.0.1:8551->8501`, datos montados de solo lectura: `/_stcore/health` = `ok` (200), estado `healthy`, usuario `app`, sin ningún `lidar_box` en el sistema de archivos.
- Camino sin Docker verificado con el entorno del repositorio (no con un entorno virtual limpio) sobre el zip desempaquetado: `PYTHONPATH=src ... streamlit run app/app.py --server.address localhost --server.port 8552`.
- Observación: al arrancar, Streamlit imprime una «External URL» con la IP pública de quien lo corre; para eso consulta un servicio externo de direcciones IP. No envía datos de la aplicación (la telemetría de uso está desactivada), pero no es cierto que el servidor no haga ninguna conexión saliente.

## 4. Cambios de código (todos mínimos; ninguna cifra, modelo, regla ni umbral cambia)
- `Dockerfile` y `.dockerignore`: la imagen incluye `docs/ep3/plan_v3.json` (sin él, las definiciones de Validación salían sin números en el contenedor).
- `app/.streamlit/config.toml`: `[client] toolbarMode = "minimal"` (la imagen mostraba el botón «Deploy»; se comprobó que ya no).
- `src/waymo_evaluacion/ep3/app_logica.py`: textos de `TEXTOS_ENTORNO["publicado"]` (abajo) y su comentario.
- `.gitignore`: `despliegue_lente.zip`.
- Pruebas ajustadas a los textos nuevos: `test_pagina_f26.py`, `test_pagina_f35.py`, `test_pagina_f36.py`; `test_readme_f38.py` y `scripts/ep3/readme_f38.py` ignoran `despliegue_lente.zip` en el árbol del README (de lo contrario el generador del README fallaría al ver el zip en la raíz). **No se tocaron `README.md` ni `scripts/generar_readme.py`.**
- Nuevos: `scripts/ep3/empaquetar_despliegue.py`, `tests/ep3/test_empaquetar_despliegue.py` (16 pruebas, solo escriben en `tmp_path`).
- Verificado antes y después: `verificar_congelados.py` 14 de 14 y `verificar_congelados_v3.py` 5 de 5; `artefactos_ep3/` y los modelos intactos.

## 5. Pruebas en la copia (la imagen construida desde el zip)
| Prueba | Resultado |
|---|---|
| `/_stcore/health` | `ok` (200), contenedor `healthy` |
| 8 páginas (Resumen, Auditoría, Cola, Validación, Explica, Puntuar, Ética, Ayuda) | todas cargan, sin excepciones |
| Puntuar `16229547658178627464_380_000_400_000` | **1 de 5** celdas marcadas, cámara 5 (225 cajas en el rango, 197 afectadas, 175 sin pareja) |
| Puntuar `10689101165701914459_2072_300_2092_300` | **0 de 5** celdas marcadas |
| `docker diff` tras puntuar | solo `/app/data` (punto de montaje): nada escrito |
| Botón «Deploy» | no aparece |

Capturas (mismas 8 páginas por CDP): `pagina_resumen.png`, `pagina_cola.png`, `pagina_auditoria.png`, `puntuar_resultado_hueco.png` (resultado de «Puntuar segmento» corriendo desde el zip en el contenedor) y `pagina_etica_modo_publicado.png`.

## 6. Textos del modo publicado (para que apruebe)
**No activado.** Interruptor exacto: variable de entorno **`EP3_ENTORNO=publicado`** (se pasa en `docker run -e EP3_ENTORNO=publicado`; sin ella la página usa los textos locales, que en EC2 serían falsos). Alternativa: `MODO_DESPLIEGUE = "publicado"` en `src/waymo_evaluacion/ep3/app_logica.py`. Con el modo activo cambian: «Dónde corre» y «Consideraciones éticas» (Ética y límites), la pregunta «¿Se guardan o se envían los archivos?» (Ayuda), y las dos etiquetas y el subtítulo de «Puntuar datos nuevos». Mientras no se aprueben, cada tarjeta de Ética lleva la marca visible **«borrador: verificar»**; para aprobarlos, poner `"borrador": ""` en `TEXTOS_ENTORNO["publicado"]` y ajustar las dos pruebas que esperan la marca (`test_pagina_f26.py`, `test_pagina_f36.py`).

Se verificó contra el código que los archivos subidos **no se escriben a disco** (la página los lee con `pd.read_parquet` sobre bytes; no hay `st.cache` sobre su contenido, ni logging, ni `to_parquet`; el ZIP de resultados se arma en memoria), y que Streamlit los guarda en memoria (`MemoryUploadedFileManager`) y los quita al cerrar la sesión (`app_session.py`). El servidor **sí recibe** el archivo.

- **Dónde corre** (Ética): «En un servidor de AWS (instancia EC2 de AWS Academy, región us-east-1), no en su equipo. La aplicación no tiene inicio de sesión: solo la abre quien llegue a su dirección, y el acceso lo restringe el grupo de seguridad de la instancia. La dirección es temporal y cambia si la instancia se detiene. No se deben subir datos que no puedan compartirse con ese servidor.»
- **Consideraciones éticas** (Ética): «Las tablas de la página tienen identificadores de objeto y marcas de tiempo, sin imágenes. El servidor SÍ recibe los archivos que se suben en «Puntuar datos nuevos»: los procesa en memoria durante la sesión, no los escribe a disco y no registra su contenido. Salen de su equipo hacia el servidor: no se deben subir datos que no puedan compartirse con él.»
- **¿Se guardan o se envían los archivos?** (Ayuda): «Los archivos que se suben salen de su equipo y llegan al servidor de la aplicación (una instancia de AWS). Allí se procesan en memoria durante la sesión: no se escriben a disco ni se registra su contenido, y se descartan al cerrar la sesión. No se deben subir datos que no puedan compartirse con ese servidor.»
- **Puntuar, subtítulo**: «Un segmento nuevo se puntúa con la solución congelada y se obtienen sus celdas marcadas y su cola de cajas; en esta página el procesamiento ocurre en el servidor.» **Etiquetas**: «Procesamiento en el servidor y en memoria» y «No se guardan los archivos» (antes decía «No se guarda nada», demasiado fuerte porque el servidor recibe el archivo).

Antes de aprobar: la frase «el acceso lo restringe el grupo de seguridad» solo es cierta si la regla del puerto 8501 no es `0.0.0.0/0`. Si se abre a todos, cambiarla.

## 7. Guía de comandos (PowerShell en Windows; instancia Amazon Linux 2023)
Reemplace `IP_PUBLICA` por la que muestra la consola de EC2 y `labsuser.pem` por el nombre de su llave (en el Learner Lab: «AWS Details» → «Download PEM»). Recomendado: tipo `t3.small` o mayor (2 GB de memoria) y disco de 16 a 20 GB; la imagen pesa 2,2 GB. Grupo de seguridad: SSH (22) y TCP 8501, ambos con origen «Mi IP».

```powershell
# 1. permisos de la llave: solo su usuario puede leerla
icacls .\labsuser.pem /inheritance:r
icacls .\labsuser.pem /grant:r "$($env:USERNAME):(R)"

# 2. su IP pública (para la regla del grupo de seguridad, con /32)
(Invoke-RestMethod https://checkip.amazonaws.com).Trim()

# 3. subir el paquete (carpeta donde esta despliegue_lente.zip)
scp -i .\labsuser.pem .\despliegue_lente.zip ec2-user@IP_PUBLICA:~/

# 4. conectarse
ssh -i .\labsuser.pem ec2-user@IP_PUBLICA
```
En la instancia (bash):
```bash
# instalar Docker y descomprimir (Ubuntu: sudo apt-get update && sudo apt-get install -y docker.io unzip; el usuario es "ubuntu")
sudo dnf install -y docker unzip
sudo systemctl enable --now docker
unzip -q despliegue_lente.zip && cd lente

# construir (3 a 6 minutos; baja python:3.10-slim y los paquetes) y correr
sudo docker build -t lente:ec2 .
sudo docker run -d --name lente --restart unless-stopped -p 8501:8501 \
  -e EP3_ENTORNO=publicado -e WAYMO_APP_DATA=/app/data/09_app_ep3 -e WAYMO_APP_MODELOS=/app/data/06_models_ep3 \
  -v "$PWD/data:/app/data:ro" lente:ec2

# comprobar
curl -s localhost:8501/_stcore/health        # debe decir: ok
sudo docker logs --tail 20 lente

# tras detener y volver a iniciar la instancia (el Learner Lab las apaga): con --restart unless-stopped y Docker habilitado
# el contenedor vuelve solo; si no, estos dos comandos:
sudo systemctl start docker
sudo docker start lente
```
Camino sin Docker (si el build falla): `python3 -m venv .venv && .venv/bin/pip install -r requirements_app.txt -c constraints_ep3.txt` y luego `PYTHONPATH=src EP3_ENTORNO=publicado .venv/bin/streamlit run app/app.py --server.address 0.0.0.0 --server.port 8501 --browser.gatherUsageStats false` (en Amazon Linux: `sudo dnf install -y python3.11 libgomp` y usar `python3.11` si el `python3` por defecto es muy nuevo o muy viejo; el entorno de desarrollo es Python 3.10).

Desde el navegador: `http://IP_PUBLICA:8501` (es `http`, no `https`). **La IP pública cambia cada vez que la instancia se detiene**, salvo que se le asigne una IP elástica (EC2 → «Direcciones IP elásticas» → asignar y asociar a la instancia). Si **su IP cambia** (otra red, otro día): consola de EC2 → «Grupos de seguridad» → el de la instancia → «Editar reglas de entrada» → en las reglas 22 y 8501 elegir «Mi IP» de nuevo → «Guardar reglas». Para la presentación: dejar la regla del 8501 solo con la IP de quien proyecta.

Después del despliegue: actualizar `docs/despliegue.json` (estado, url, fecha, modo `publicado`) y regenerar el README (`contar_pruebas.py` → `medir_pruebas_ep3.py` → `generar_readme.py`); el número de pruebas que cita el README (415) es anterior a las 16 nuevas (431 en total).

## 8. Qué NO pude verificar
- Nada en AWS real: ni el arranque de la instancia, ni el build en Amazon Linux 2023 (tiempo, memoria y disco reales), ni las reglas del grupo de seguridad, ni la IP elástica, ni que el Learner Lab permita todo esto.
- Los comandos de instalación de Docker en Amazon Linux/Ubuntu y el reinicio con `--restart unless-stopped` tras detener la instancia (en la prueba local el contenedor se corrió sin política de reinicio).
- `--server.address 0.0.0.0` directo en esta máquina (ver aviso 3) y un entorno virtual limpio desde cero (el camino sin Docker se probó con el entorno del repositorio).
- La descarga de la imagen base desde el servidor de AWS (en esta máquina sí funcionó).
- Subidas grandes con conexiones lentas desde el navegador de la presentación: se probó con los dos archivos reales de la demostración (1,7 MB y 0,7 MB) desde el mismo equipo.
- El README no se tocó: sigue diciendo que el despliegue está «en preparación» y 415 pruebas.

## Diff de los cambios de código (archivos versionados)
```diff
diff --git a/.dockerignore b/.dockerignore
--- a/.dockerignore
+++ b/.dockerignore
@@ -24,3 +24,6 @@ tests/
 # Datos de la demostracion en vivo (F37): nunca dentro de la imagen
 datos_demo/
 **/datos_demo/
+
+# unico archivo de docs/ que entra a la imagen (F43): el plan v3 congelado, que la pagina lee en solo lectura
+!docs/ep3/plan_v3.json
diff --git a/.gitignore b/.gitignore
--- a/.gitignore
+++ b/.gitignore
@@ -188,5 +188,8 @@ entrega_EP3.zip
 docs/ep3/revision/
 entrega_EP3.sha256
 
+# Paquete de despliegue en EC2 (scripts/ep3/empaquetar_despliegue.py)
+despliegue_lente.zip
+
 # Datos de la demostracion en vivo (F37): segmentos reales descargados del bucket y variantes simuladas; no se versionan ni van en la imagen
 datos_demo/
diff --git a/Dockerfile b/Dockerfile
--- a/Dockerfile
+++ b/Dockerfile
@@ -1,4 +1,4 @@
-# Pagina de EP3 (solo local). NO se hornean datos en la imagen: data/ se monta como volumen de solo lectura.
+# Pagina de EP3 (local o en EC2). NO se hornean datos en la imagen: data/ se monta como volumen de solo lectura (en EC2: -v $PWD/data:/app/data:ro).
 FROM python:3.10-slim
 
 ENV PYTHONDONTWRITEBYTECODE=1 \
@@ -23,6 +23,8 @@ COPY app ./app
 COPY app/.streamlit ./.streamlit
 COPY src/waymo_evaluacion/__init__.py ./src/waymo_evaluacion/__init__.py
 COPY src/waymo_evaluacion/ep3 ./src/waymo_evaluacion/ep3
+# plan v3 congelado (un solo archivo de solo lectura): la pagina lee de el los umbrales que muestra; sin el, esas definiciones salen sin numeros
+COPY docs/ep3/plan_v3.json ./docs/ep3/plan_v3.json
 
 USER app
 EXPOSE 8501
diff --git a/app/.streamlit/config.toml b/app/.streamlit/config.toml
--- a/app/.streamlit/config.toml
+++ b/app/.streamlit/config.toml
@@ -6,6 +6,9 @@ headless = true
 enableXsrfProtection = true
 maxUploadSize = 500
 
+[client]
+toolbarMode = "minimal"
+
 # Tema (F24): oscuro, generado desde TOKENS de app/estilos.py con scripts/ep3/generar_config_tema.py (no editar a mano); tipografia del sistema, sin fuentes externas.
 [theme]
 base = "dark"
diff --git a/scripts/ep3/generar_mapa.py b/scripts/ep3/generar_mapa.py
--- a/scripts/ep3/generar_mapa.py
+++ b/scripts/ep3/generar_mapa.py
@@ -239,6 +239,7 @@ DESC: dict[str, tuple[str, str, str]] = {
     "scripts/ep3/f39_regresion.py": ("F39: guarda y compara los hash de los CSV de resultados y las cifras de pantalla de los 4 segmentos reales (con y sin archivo 2) y del ejemplo, con la misma función de la página.", "Regresión de F39", "el ZIP lleva la hora de creación: se comparan los CSV de adentro"),
     "scripts/ep3/f39_tiempos.py": ("F39: tiempos de Puntuar en el navegador real (flujo anterior y flujo nuevo), 3 repeticiones por segmento.", "Para el reporte de F39", "con la página corriendo"),
     "scripts/ep3/f39_pruebas_ui.py": ("F39: pruebas de estado del flujo nuevo con los cargadores reales (11 casos) y las 8 capturas de revisión.", "Para el reporte de F39", "con la página corriendo; reemplaza a `f37_pruebas_ui.py`"),
+    "scripts/ep3/empaquetar_despliegue.py": ("F43: arma `despliegue_lente.zip` (código, artefactos, configuración, Dockerfile y los datos mínimos que la página abre) para subirlo por scp a EC2; falla si encuentra datos crudos de Waymo, `datos_demo/` o `data/` fuera de la lista.", "Despliegue en EC2", "el zip no se versiona (.gitignore)"),
     "scripts/ep3/f40_prueba_segmentos_nuevos.py": ("F40: puntúa los 4 segmentos nuevos reales de `datos_demo/candidatos/` con las mismas funciones de la página y escribe `docs/ep3/prueba_segmentos_nuevos.json`.", "Prueba de funcionamiento del README", "necesita `datos_demo/` (no se versiona)"),
     "docs/ep3/prueba_segmentos_nuevos.json": ("F40: resultado de la prueba con 4 segmentos nuevos reales (cajas, celdas marcadas, sha256 de los archivos de entrada). No es una validación estadística.", "Fuente de la sección 16 del README", "lo genera f40_prueba_segmentos_nuevos.py"),
     "docs/ep3/f39_regresion_antes.json": ("F39: resultados de los casos de regresión ANTES de cambiar el flujo.", "Fuente del reporte", "no se regenera"),
diff --git a/scripts/ep3/readme_f38.py b/scripts/ep3/readme_f38.py
--- a/scripts/ep3/readme_f38.py
+++ b/scripts/ep3/readme_f38.py
@@ -546,7 +546,7 @@ GRUPOS_ARCHIVOS = [(["Dockerfile", "docker-compose.yml", ".dockerignore", "requi
 def arbol_repo() -> str:
     """Árbol de la raíz generado del sistema de archivos: si aparece una carpeta o un archivo sin descripción, el generador falla en vez de omitirlo."""
     ocultos = {".git", ".venv", "__pycache__", ".pytest_cache", ".ipynb_checkpoints", ".viz", ".mypy_cache", "node_modules"}
-    reales = [p for p in RAIZ.iterdir() if p.name not in ocultos and not p.name.startswith(".coverage") and p.name != "info.log"]      # restos de ejecutar pytest (cobertura y registro de Kedro), no del proyecto
+    reales = [p for p in RAIZ.iterdir() if p.name not in ocultos and not p.name.startswith(".coverage") and p.name not in ("info.log", "despliegue_lente.zip")]      # restos de ejecutar pytest (cobertura y registro de Kedro), no del proyecto
     claves = {p.name + ("/" if p.is_dir() else "") for p in reales}
     agrupados = {a for g, _ in GRUPOS_ARCHIVOS for a in g}
     sin_desc = sorted(claves - set(DIRS_RAIZ) - agrupados)
diff --git a/src/waymo_evaluacion/ep3/app_logica.py b/src/waymo_evaluacion/ep3/app_logica.py
--- a/src/waymo_evaluacion/ep3/app_logica.py
+++ b/src/waymo_evaluacion/ep3/app_logica.py
@@ -345,8 +345,8 @@ DESCRIPCION_PAGINA = {"Cola de revisión": "Qué cajas revisar y en qué orden.
                       "Ética y límites": "Ficha del sistema: propósito, datos, desempeño, límites, consideraciones éticas y entorno de ejecución.",
                       "Ayuda y glosario": "Flujo de revisión, glosario y preguntas frecuentes."}
 # F26-B1 y F36: textos que dependen de cómo se despliega la página. UNA sola constante, ``MODO_DESPLIEGUE``, decide cuáles se muestran: ``local`` (por defecto) dice lo que es verdad en el equipo de la persona;
-# ``publicado`` es la variante para cuando la página se publique en internet. **No está activada**: sus textos son borradores («borrador: verificar») y llevan un hueco, ``[nombre del servicio]``, que hay que
-# completar y comprobar antes de usarla. Para probarla sin tocar el archivo se puede fijar la variable de entorno ``EP3_ENTORNO=publicado`` (también acepta ``servidor``); la variable manda sobre la constante.
+# ``publicado`` es la variante para la instancia EC2 de AWS Academy (F43: redactada contra cómo corre ahí). **No está activada** hasta que el equipo apruebe sus textos: mientras tanto llevan la marca visible «borrador: verificar» (clave ``borrador``), que hay que
+# quitar (dejarla vacía) al aprobarlos. Para probarla sin tocar el archivo se puede fijar la variable de entorno ``EP3_ENTORNO=publicado`` (también acepta ``servidor``); la variable manda sobre la constante.
 # Los archivos cargados NO se escriben a disco: ``puntuar_segmento`` trabaja en memoria y la página no llama a ``guardar`` (lo vigila una prueba).
 MODO_DESPLIEGUE = "local"
 MODOS_DESPLIEGUE = ("local", "publicado")
@@ -361,12 +361,12 @@ TEXTOS_ENTORNO = {
         "borrador": "",
     },
     "publicado": {
-        "donde_corre": "En un servidor conectado a internet ([nombre del servicio]). Cualquiera que tenga el enlace puede abrir la aplicación. No se deben subir datos que no puedan compartirse con ese servicio.",
+        "donde_corre": "En un servidor de AWS (instancia EC2 de AWS Academy, región us-east-1), no en su equipo. La aplicación no tiene inicio de sesión: solo la abre quien llegue a su dirección, y el acceso lo restringe el grupo de seguridad de la instancia. La dirección es temporal y cambia si la instancia se detiene. No se deben subir datos que no puedan compartirse con ese servidor.",
         "puntuar_subtitulo": "Un segmento nuevo se puntúa con la solución congelada y se obtienen sus celdas marcadas y su cola de cajas; en esta página el procesamiento ocurre en el servidor.",
         "puntuar_etiqueta": "Procesamiento en el servidor y en memoria",
-        "puntuar_etiqueta_2": "No se guarda nada",
-        "consideracion_etica": "Las tablas tienen identificadores de objeto y marcas de tiempo. Los archivos que se suben en «Puntuar datos nuevos» se procesan en la memoria del servidor durante la sesión y no se guardan.",
-        "faq_archivos": "Los archivos que se suben se procesan en la memoria del servidor durante la sesión y no se guardan. Salen del equipo hacia el servidor, así que no se deben subir datos que no puedan compartirse con él.",
+        "puntuar_etiqueta_2": "No se guardan los archivos",
+        "consideracion_etica": "Las tablas de la página tienen identificadores de objeto y marcas de tiempo, sin imágenes. El servidor SÍ recibe los archivos que se suben en «Puntuar datos nuevos»: los procesa en memoria durante la sesión, no los escribe a disco y no registra su contenido. Salen de su equipo hacia el servidor: no se deben subir datos que no puedan compartirse con él.",
+        "faq_archivos": "Los archivos que se suben salen de su equipo y llegan al servidor de la aplicación (una instancia de AWS). Allí se procesan en memoria durante la sesión: no se escriben a disco ni se registra su contenido, y se descartan al cerrar la sesión. No se deben subir datos que no puedan compartirse con ese servidor.",
         "borrador": "borrador: verificar",
     },
 }
```

Los cambios en pruebas (test_pagina_f26/f35/f36, test_readme_f38) solo reemplazan los textos esperados del modo publicado y la lista de archivos que el árbol del README ignora; ver `git diff -- tests/ep3`.
