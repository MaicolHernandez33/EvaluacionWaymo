"""Detector de huecos por cámara (apéndice M del notebook 10, extraído a funciones puras).

Un «hueco» es una celda (segmento, cámara) donde la tasa de cajas con par 2D es muy
inferior a la mediana de esa cámara entre segmentos, medida dentro del rango de azimut
propio de la cámara. La lógica replica las celdas 46 y 52 del notebook
``10_evaluacion_final_sin_camara.ipynb``.

Convenciones de columnas de ``cajas``:
    ``segment_id`` (identificador completo), ``seg`` (identificador corto, 12 caracteres),
    ``grupo`` («train» o «test»), ``location``, ``time_of_day``, ``sin_camara`` (0 o 1),
    ``az_signed`` (azimut con signo en grados) y, tras ``agregar_pares_camara``,
    ``c1`` a ``c5`` (1 si la caja tiene par en esa cámara).

Ninguna función escribe archivos ni imprime; las rutas llegan por argumento.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

Rangos = dict[int, tuple[float, float]]

COL_TIMESTAMP = "key.frame_timestamp_micros"
COL_OBJETO = "key.laser_object_id"
COL_CAMARA = "key.camera_name"


def _cols_camara(camaras: Sequence[int]) -> list[str]:
    """Nombres de columna ``c1``, ``c2``... para una lista de cámaras."""
    return [f"c{c}" for c in camaras]


def azimut_con_signo(x: Any, y: Any) -> Any:
    """Azimut con signo, en grados, de un punto (x, y): ``degrees(arctan2(y, x))``.

    Args:
        x: coordenada x del centro de la caja (escalar, arreglo o Serie).
        y: coordenada y del centro de la caja.

    Returns:
        Azimut en grados, entre -180 y 180, con el mismo tipo de contenedor que la entrada.
    """
    return np.degrees(np.arctan2(y, x))


def agregar_pares_camara(
    cajas: pd.DataFrame,
    ruta_asociacion: Path,
    camaras: Sequence[int],
    col_segmento: str = "segment_id",
) -> pd.DataFrame:
    """Agrega las columnas ``c1``..``cN`` con el par de cada caja en cada cámara.

    Por cada segmento lee ``{ruta_asociacion}/{segmento}.parquet``, pivotea
    ``key.camera_name`` a columnas y une por (timestamp, objeto). Las cajas sin
    asociación quedan con 0. El resultado conserva el orden por segmento del cálculo
    original (agrupación sin ordenar).

    Args:
        cajas: tabla de cajas con ``segment_id``, ``key.frame_timestamp_micros``,
            ``key.laser_object_id`` y ``sin_camara``.
        ruta_asociacion: carpeta con los parquet de ``camera_to_lidar_box_association``.
        camaras: números de cámara (por ejemplo ``[1, 2, 3, 4, 5]``).
        col_segmento: columna con el identificador completo del segmento.

    Returns:
        Copia de ``cajas`` con las columnas ``c{n}`` enteras.

    Raises:
        ValueError: si «tiene par en alguna cámara» no coincide con ``sin_camara == 0``.
    """
    camaras = sorted(camaras)
    cols = _cols_camara(camaras)
    partes = []
    for segmento, grupo in cajas.groupby(col_segmento, sort=False):
        asoc = pd.read_parquet(
            Path(ruta_asociacion) / f"{segmento}.parquet",
            columns=[COL_TIMESTAMP, COL_CAMARA, COL_OBJETO],
        ).drop_duplicates()
        pares = (
            asoc.assign(v=1)
            .pivot_table(
                index=[COL_TIMESTAMP, COL_OBJETO],
                columns=COL_CAMARA,
                values="v",
                aggfunc="max",
                fill_value=0,
            )
            .reindex(columns=camaras, fill_value=0)
        )
        pares.columns = cols
        partes.append(grupo.merge(pares.reset_index(), on=[COL_TIMESTAMP, COL_OBJETO], how="left"))
    salida = pd.concat(partes, ignore_index=True)
    for col in cols:
        salida[col] = salida[col].fillna(0).astype(int)
    if not ((salida[cols].sum(axis=1) > 0) == (salida["sin_camara"] == 0)).all():
        raise ValueError("el par por camara no coincide con sin_camara")
    return salida


def calcular_rangos(
    cajas_train: pd.DataFrame,
    camaras: Sequence[int],
    p_inf: float = 5,
    p_sup: float = 95,
    col_azimut: str = "az_signed",
) -> Rangos:
    """Rango de azimut con signo de cada cámara (percentiles ``p_inf`` a ``p_sup``).

    Usa solo las cajas que tienen par en esa cámara. Debe recibir únicamente cajas de
    entrenamiento, para no filtrar información del test.

    Args:
        cajas_train: cajas de entrenamiento con ``c{n}`` y la columna de azimut.
        camaras: números de cámara.
        p_inf: percentil inferior.
        p_sup: percentil superior.
        col_azimut: columna con el azimut con signo.

    Returns:
        Diccionario ``{cámara: (azimut_inferior, azimut_superior)}``.

    Raises:
        ValueError: si una cámara no tiene ninguna caja con par.
    """
    rangos: Rangos = {}
    for c in camaras:
        az = cajas_train.loc[cajas_train[f"c{c}"] == 1, col_azimut]
        if az.empty:
            raise ValueError(f"la camara {c} no tiene cajas con par para calcular el rango")
        rangos[c] = (float(np.percentile(az, p_inf)), float(np.percentile(az, p_sup)))
    return rangos


def tasa_por_celda(
    cajas: pd.DataFrame,
    rangos: Mapping[int, tuple[float, float]],
    camaras: Sequence[int],
    col_segmento: str = "seg",
    col_azimut: str = "az_signed",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Tasa de cajas con par y número de cajas en el rango, por segmento y cámara.

    Para cada cámara considera solo las cajas cuyo azimut cae dentro de su rango
    (extremos incluidos). La tasa es NaN si el segmento no tiene cajas en el rango.

    Args:
        cajas: cajas con ``c{n}``, azimut y segmento corto.
        rangos: rango de azimut de cada cámara.
        camaras: números de cámara.
        col_segmento: columna con el segmento corto.
        col_azimut: columna con el azimut con signo.

    Returns:
        ``(tasa, nrango)``: dos tablas indexadas por segmento, con columnas ``c{n}``.
    """
    indice = cajas.groupby(col_segmento).size().index
    tasa: dict[str, pd.Series] = {}
    nrango: dict[str, pd.Series] = {}
    for c in camaras:
        en = (cajas[col_azimut] >= rangos[c][0]) & (cajas[col_azimut] <= rangos[c][1])
        g = cajas[en].groupby(col_segmento)[f"c{c}"].agg(["mean", "size"])
        tasa[f"c{c}"] = g["mean"].reindex(indice).astype(float)
        nrango[f"c{c}"] = g["size"].reindex(indice).fillna(0).astype(int)
    return pd.DataFrame(tasa, index=indice), pd.DataFrame(nrango, index=indice)


def calcular_medianas(tasa: pd.DataFrame) -> pd.Series:
    """Mediana de la tasa de cada cámara entre segmentos (ignora los NaN).

    Args:
        tasa: tabla de ``tasa_por_celda``.

    Returns:
        Serie indexada por ``c{n}``.
    """
    return tasa.median()


def detectar_huecos(
    tasa: pd.DataFrame,
    nrango: pd.DataFrame,
    medianas: Mapping[str, float] | pd.Series | None = None,
    frac: float = 0.25,
    min_cajas: int = 100,
) -> pd.DataFrame:
    """Marca las celdas (segmento, cámara) con hueco.

    Hay hueco si ``tasa < frac * mediana`` y el segmento tiene al menos ``min_cajas``
    cajas en el rango de la cámara.

    Args:
        tasa: tabla de tasas por segmento y cámara.
        nrango: tabla de cajas en el rango.
        medianas: medianas de referencia por cámara (por ejemplo, las congeladas de
            EP2). Si es None se calculan de la propia ``tasa``, como en EP2.
        frac: fracción de la mediana bajo la cual la tasa se considera hueco.
        min_cajas: mínimo de cajas en el rango para poder declarar un hueco.

    Returns:
        Tabla booleana con las mismas columnas ``c{n}`` que ``tasa``.
    """
    med = calcular_medianas(tasa) if medianas is None else pd.Series(dict(medianas), dtype=float)
    return pd.DataFrame(
        {col: (tasa[col] < frac * med[col]) & (nrango[col] >= min_cajas) for col in tasa.columns}
    )


def marcar_cajas_en_hueco(
    cajas: pd.DataFrame,
    huecos: pd.DataFrame,
    rangos: Mapping[int, tuple[float, float]],
    col_segmento: str = "seg",
    col_azimut: str = "az_signed",
) -> pd.Series:
    """Indica qué cajas están en una celda con hueco, dentro del rango de esa cámara.

    Equivale a ``en_celda_hueco`` del notebook: una caja se marca si su segmento tiene
    hueco en alguna cámara y su azimut cae en el rango de esa cámara. Los segmentos
    que no están en ``huecos`` no se marcan.

    Args:
        cajas: cajas con segmento corto y azimut con signo.
        huecos: tabla booleana de ``detectar_huecos`` (columnas ``c{n}``).
        rangos: rango de azimut de cada cámara.
        col_segmento: columna con el segmento corto.
        col_azimut: columna con el azimut con signo.

    Returns:
        Serie booleana con el índice de ``cajas``.
    """
    salida = np.zeros(len(cajas), dtype=bool)
    azimut = cajas[col_azimut].to_numpy()
    for seg, pos in cajas.groupby(col_segmento).indices.items():
        if seg not in huecos.index:
            continue
        for c in rangos:
            if bool(huecos.loc[seg, f"c{c}"]):
                az = azimut[pos]
                salida[pos] |= (az >= rangos[c][0]) & (az <= rangos[c][1])
    return pd.Series(salida, index=cajas.index, name="en_hueco")


@dataclass
class ParametrosDetector:
    """Parámetros del detector, serializables a JSON.

    Attributes:
        frac: fracción de la mediana que define el hueco.
        min_cajas: mínimo de cajas en el rango para declarar un hueco.
        p_inf: percentil inferior del rango de azimut.
        p_sup: percentil superior del rango de azimut.
        rangos: rango de azimut por cámara (None si aún no se calculó).
        medianas_ref: medianas de referencia por ``c{n}`` (None: se recalculan).
    """

    frac: float = 0.25
    min_cajas: int = 100
    p_inf: float = 5
    p_sup: float = 95
    rangos: Rangos | None = None
    medianas_ref: dict[str, float] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Diccionario compatible con ``json.dumps`` (claves de cámara como texto)."""
        return {
            "frac": self.frac,
            "min_cajas": self.min_cajas,
            "p_inf": self.p_inf,
            "p_sup": self.p_sup,
            "rangos": None
            if self.rangos is None
            else {str(c): [float(v[0]), float(v[1])] for c, v in self.rangos.items()},
            "medianas_ref": None
            if self.medianas_ref is None
            else {str(k): float(v) for k, v in self.medianas_ref.items()},
        }

    @classmethod
    def from_dict(cls, datos: Mapping[str, Any]) -> ParametrosDetector:
        """Reconstruye los parámetros desde ``to_dict`` (o su versión leída de JSON)."""
        rangos = datos.get("rangos")
        medianas = datos.get("medianas_ref")
        return cls(
            frac=float(datos.get("frac", 0.25)),
            min_cajas=int(datos.get("min_cajas", 100)),
            p_inf=float(datos.get("p_inf", 5)),
            p_sup=float(datos.get("p_sup", 95)),
            rangos=None
            if rangos is None
            else {int(c): (float(v[0]), float(v[1])) for c, v in rangos.items()},
            medianas_ref=None
            if medianas is None
            else {str(k): float(v) for k, v in medianas.items()},
        )


def resumen_celdas(
    cajas: pd.DataFrame,
    tasa: pd.DataFrame,
    nrango: pd.DataFrame,
    huecos: pd.DataFrame,
    col_segmento: str = "seg",
) -> pd.DataFrame:
    """Tabla segmento por cámara igual a ``10_M_tasa_segmento_camara.csv``.

    Columnas (con ``seg`` como índice): ``grupo``, ``ubicacion``, ``momento``, ``cajas``,
    ``tasa_c{n}``, ``n_rango_c{n}``, ``hueco_c{n}`` y ``algun_hueco``. Ordenada por
    grupo descendente, ubicación y momento.

    Args:
        cajas: cajas con ``grupo``, ``location``, ``time_of_day`` y ``sin_camara``.
        tasa: tabla de ``tasa_por_celda``.
        nrango: tabla de ``tasa_por_celda``.
        huecos: tabla de ``detectar_huecos``.
        col_segmento: columna con el segmento corto.

    Returns:
        Tabla resumen por segmento.
    """
    meta = cajas.groupby(col_segmento).agg(
        grupo=("grupo", "first"),
        ubicacion=("location", "first"),
        momento=("time_of_day", "first"),
        cajas=("sin_camara", "size"),
    )
    tabla = (
        meta.join(tasa.add_prefix("tasa_"))
        .join(nrango.add_prefix("n_rango_"))
        .join(huecos.add_prefix("hueco_"))
    )
    tabla["algun_hueco"] = huecos.any(axis=1)
    return tabla.sort_values(["grupo", "ubicacion", "momento"], ascending=[False, True, True])
