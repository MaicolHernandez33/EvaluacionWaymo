"""Inferencia de EP3: de un segmento (lidar_box + asociación opcional) a las listas A y B.

Flujo en dos pasos (con una persona que revisa y decide al final):
  1. Filtro 1 (detector): con los rangos y medianas congelados, marca las celdas (segmento, cámara)
     con hueco: la Lista A, que se atiende aparte.
  2. Modelo o regla congelados: ordenan las cajas de las celdas sanas: la Lista B.
Sin asociación solo se puede puntuar (no hay detector ni etiqueta). No escribe archivos.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from .detector_huecos import ParametrosDetector, detectar_huecos, marcar_cajas_en_hueco, tasa_por_celda

VRU = ("PEDESTRIAN", "CYCLIST")
TIPOS = {1: "VEHICLE", 2: "PEDESTRIAN", 3: "SIGN", 4: "CYCLIST"}
CAMARAS = [1, 2, 3, 4, 5]
NOMBRE_CAMARA = {1: "1 (frontal)", 2: "2 (frontal izq.)", 3: "3 (frontal der.)", 4: "4 (lateral izq.)", 5: "5 (lateral der.)"}
V16 = ["box_center_x", "box_center_y", "box_center_z", "azimut_abs_deg", "distancia_m", "box_length", "box_width", "box_height", "volumen_caja",
       "num_lidar_points", "num_top_lidar_points", "densidad_puntos", "speed_mps", "heading_sin", "heading_cos", "es_ciclista"]
LLAVE = ["key.frame_timestamp_micros", "key.laser_object_id"]


@dataclass
class Artefactos:
    """Solución congelada: puntuador, calibrador, umbrales y parámetros del detector."""

    puntuador: Any
    calibrador: Any
    umbrales: dict[str, float]
    detector: ParametrosDetector
    descripcion: dict[str, Any] = field(default_factory=dict)

    def guardar(self, carpeta: Path) -> None:
        """Escribe ``modelo_final_v3.joblib``, ``umbrales_v3.json`` y ``detector_params_v3.json`` en ``carpeta``."""
        carpeta.mkdir(parents=True, exist_ok=True)
        joblib.dump({"puntuador": self.puntuador, "calibrador": self.calibrador, "descripcion": self.descripcion}, carpeta / "modelo_final_v3.joblib")
        (carpeta / "umbrales_v3.json").write_text(json.dumps(self.umbrales, indent=1), encoding="utf-8")
        (carpeta / "detector_params_v3.json").write_text(json.dumps(self.detector.to_dict(), ensure_ascii=False, indent=1), encoding="utf-8")


def cargar_artefactos(carpeta: Path) -> Artefactos:
    """Carga la solución congelada desde ``carpeta`` (por ejemplo ``data/06_models_ep3``)."""
    d = joblib.load(carpeta / "modelo_final_v3.joblib")
    umbrales = json.loads((carpeta / "umbrales_v3.json").read_text(encoding="utf-8"))
    det = ParametrosDetector.from_dict(json.loads((carpeta / "detector_params_v3.json").read_text(encoding="utf-8")))
    return Artefactos(d["puntuador"], d["calibrador"], umbrales, det, d.get("descripcion", {}))


def _col(df: pd.DataFrame, sufijo: str, obligatoria: bool = True) -> str | None:
    for c in df.columns:
        if c.endswith(sufijo):
            return c
    if obligatoria:
        raise KeyError(f"falta una columna que termine en {sufijo!r} en lidar_box")
    return None


def construir_variables(lidar_box: pd.DataFrame) -> pd.DataFrame:
    """Variables de EP2 desde un parquet crudo de ``lidar_box`` (mismas fórmulas que la ingesta de EP2).

    Devuelve las llaves, ``segment_id``, ``object_type`` y las 16 variables.
    """
    df = pd.DataFrame({"segment_id": lidar_box[_col(lidar_box, "key.segment_context_name")].astype(str)})
    df[LLAVE[0]] = lidar_box[LLAVE[0]].to_numpy()
    df[LLAVE[1]] = lidar_box[LLAVE[1]].to_numpy()
    mapa = {"box_center_x": "box.center.x", "box_center_y": "box.center.y", "box_center_z": "box.center.z", "box_length": "box.size.x",
            "box_width": "box.size.y", "box_height": "box.size.z", "num_lidar_points": "num_lidar_points_in_box",
            "num_top_lidar_points": "num_top_lidar_points_in_box"}
    for k, suf in mapa.items():
        df[k] = lidar_box[_col(lidar_box, suf)].to_numpy()
    df["object_type"] = lidar_box[_col(lidar_box, "].type")].map(TIPOS).to_numpy()
    vx, vy = _col(lidar_box, "speed.x", False), _col(lidar_box, "speed.y", False)
    df["speed_mps"] = np.hypot(lidar_box[vx], lidar_box[vy]).to_numpy() if vx and vy else np.nan
    rumbo = lidar_box[_col(lidar_box, "box.heading")].to_numpy(dtype=float)
    df["heading_sin"], df["heading_cos"] = np.sin(rumbo), np.cos(rumbo)
    df["distancia_m"] = np.sqrt(df["box_center_x"] ** 2 + df["box_center_y"] ** 2)
    df["volumen_caja"] = df["box_length"] * df["box_width"] * df["box_height"]
    df["densidad_puntos"] = (df["num_lidar_points"] / df["volumen_caja"]).replace([np.inf, -np.inf], np.nan)
    df["azimut_abs_deg"] = np.abs(np.degrees(np.arctan2(df["box_center_y"], df["box_center_x"])))
    df["az_signed"] = np.degrees(np.arctan2(df["box_center_y"], df["box_center_x"]))
    df["es_ciclista"] = (df["object_type"] == "CYCLIST").astype(int)
    return df


def agregar_asociacion(cajas: pd.DataFrame, asociacion: pd.DataFrame, camaras: list[int] = CAMARAS) -> pd.DataFrame:
    """Agrega ``c1``..``c5``, ``sin_camara`` y descarta los frames sin ninguna etiqueta de cámara (igual que EP2)."""
    a = asociacion[[LLAVE[0], "key.camera_name", LLAVE[1]]].drop_duplicates()
    pares = (a.assign(v=1).pivot_table(index=LLAVE, columns="key.camera_name", values="v", aggfunc="max", fill_value=0)
             .reindex(columns=camaras, fill_value=0))
    pares.columns = [f"c{c}" for c in camaras]
    out = cajas.merge(pares.reset_index(), on=LLAVE, how="left")
    cols = [f"c{c}" for c in camaras]
    out[cols] = out[cols].fillna(0).astype(int)
    out["sin_camara"] = (out[cols].sum(axis=1) == 0).astype(int)
    con_par = out.groupby(LLAVE[0])["sin_camara"].transform(lambda s: (s == 0).any())
    return out[con_par].reset_index(drop=True)


@dataclass
class ResultadoSegmento:
    """Salida de ``puntuar_segmento``."""

    cajas: pd.DataFrame            # cajas VRU de la población principal, con score, probabilidad y marca de hueco
    lista_A: pd.DataFrame          # celdas (segmento, cámara) con hueco
    lista_B: pd.DataFrame          # cajas de celdas sanas, ordenadas de mayor a menor puntaje
    tasas: pd.DataFrame            # tasa y cajas en rango por segmento y cámara
    resumen: dict[str, Any]
    advertencias: list[str]


def puntuar_segmento(lidar_box: pd.DataFrame, asociacion: pd.DataFrame | None, art: Artefactos, az_max: float = 100.0) -> ResultadoSegmento:
    """Puntúa un segmento (o varios) con la solución congelada y arma las listas A y B.

    Args:
        lidar_box: parquet crudo de ``lidar_box`` ya leído.
        asociacion: parquet crudo de ``camera_to_lidar_box_association`` (opcional).
        art: artefactos congelados.
        az_max: azimut máximo de la población principal.
    """
    adv: list[str] = []
    todo = construir_variables(lidar_box)
    vru = todo[todo["object_type"].isin(VRU) & (todo["azimut_abs_deg"] <= 120)].reset_index(drop=True)
    if vru.empty:
        raise ValueError("no hay peatones ni ciclistas dentro de 120 grados en lidar_box")
    if vru[V16].isna().any().any():
        adv.append("hay valores faltantes en alguna variable; esas cajas se puntúan con el valor que devuelva el modelo o se omiten")
        vru = vru.dropna(subset=V16).reset_index(drop=True)
    vru["seg"] = vru["segment_id"].str[:12]
    tasas = pd.DataFrame()
    lista_a = pd.DataFrame(columns=["segmento", "camara", "tasa", "mediana_referencia", "umbral", "cajas_en_rango", "cajas_afectadas"])
    vru["en_hueco"] = False
    tiene_asoc = asociacion is not None and len(asociacion) > 0
    if tiene_asoc:
        vru = agregar_asociacion(vru, asociacion)
        det = art.detector
        rangos = det.rangos or {}
        medianas = det.medianas_ref or {}
        if rangos and medianas:
            tasa, nrango = tasa_por_celda(vru, rangos, list(rangos))
            huecos = detectar_huecos(tasa, nrango, medianas, det.frac, det.min_cajas)
            vru["en_hueco"] = marcar_cajas_en_hueco(vru, huecos, rangos).to_numpy()
            tasas = pd.concat({"tasa": tasa, "cajas_en_rango": nrango}, axis=1)
            filas = []
            for s in huecos.index:
                for c in rangos:
                    if huecos.loc[s, f"c{c}"]:
                        afect = vru[(vru["seg"] == s) & vru["az_signed"].between(*rangos[c]) & (vru["azimut_abs_deg"] <= az_max)]
                        filas.append({"segmento": s, "camara": NOMBRE_CAMARA[c], "tasa": float(tasa.loc[s, f"c{c}"]), "mediana_referencia": float(medianas[f"c{c}"]),
                                      "umbral": float(det.frac * medianas[f"c{c}"]), "cajas_en_rango": int(nrango.loc[s, f"c{c}"]), "cajas_afectadas": len(afect)})
            if filas:
                lista_a = pd.DataFrame(filas)
        else:
            adv.append("los parámetros del detector no traen rangos y medianas congelados: no se pudo buscar huecos")
    else:
        adv.append("sin archivo de asociación: se puntúan las cajas pero no se puede buscar huecos de cámara ni conocer sin_camara")
    ppal = vru[vru["azimut_abs_deg"] <= az_max].reset_index(drop=True)
    ppal["score"] = art.puntuador.puntuar(ppal)
    ppal["prob_calibrada"] = art.calibrador.calibrar(ppal["score"].to_numpy()) if art.calibrador is not None else np.nan
    cola = ppal[~ppal["en_hueco"]].sort_values("score", ascending=False, kind="stable")
    ppal["posicion_en_cola"] = np.nan
    ppal.loc[cola.index, "posicion_en_cola"] = np.arange(1, len(cola) + 1)
    ppal["percentil_en_cola"] = ppal["posicion_en_cola"] / max(len(cola), 1)
    lista_b = ppal.loc[cola.index].sort_values("posicion_en_cola")
    cols_base = ["segment_id", "seg", LLAVE[0], LLAVE[1], "object_type", "azimut_abs_deg", "distancia_m", "num_lidar_points", "num_top_lidar_points",
                 "score", "prob_calibrada", "en_hueco", "posicion_en_cola", "percentil_en_cola"]
    cols_base += [c for c in ("sin_camara",) if c in ppal.columns]
    resumen = {
        "cajas_vru_poblacion_principal": int(len(ppal)), "cajas_en_celdas_con_hueco": int(ppal["en_hueco"].sum()), "cajas_en_lista_B": int(len(lista_b)),
        "celdas_con_hueco": int(len(lista_a)), "tiene_asociacion": bool(tiene_asoc),
        "umbral_A": art.umbrales.get("A"), "umbral_B": art.umbrales.get("B"),
    }
    if "sin_camara" in ppal.columns:
        resumen["positivos_total"] = int(ppal["sin_camara"].sum())
        resumen["positivos_en_celdas_con_hueco"] = int(ppal.loc[ppal["en_hueco"], "sin_camara"].sum())
    return ResultadoSegmento(ppal[cols_base + [c for c in ppal.columns if c.startswith("c") and c[1:].isdigit()]], lista_a, lista_b[cols_base], tasas, resumen, adv)


def percentil_en_referencia(score: float, referencia: np.ndarray) -> float:
    """Fracción de la referencia con puntaje mayor o igual al dado (0 = el más alto de la cola, 1 = el más bajo)."""
    ref = np.asarray(referencia, dtype=float)
    return float((ref >= score).mean())
