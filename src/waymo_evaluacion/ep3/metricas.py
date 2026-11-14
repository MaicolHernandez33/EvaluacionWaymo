"""Métricas de ranking y de punto de operación, con bootstrap por segmentos.

Las definiciones siguen a EP2 (notebook 10): Captura@20 % es la fracción de positivos que cae
en el 20 % de cajas mejor puntuadas; Fracción para 80 % es la fracción de cajas que hay que
revisar para capturar el 80 % de los positivos; ECE usa 10 cuantiles de la probabilidad.

El bootstrap por segmentos se hace con pesos: cada réplica da un peso entero a cada segmento
(cuántas veces salió) y todas las métricas se calculan con filas ponderadas, sin copiar datos.
Las diferencias entre métodos son pareadas (mismos pesos para todos).
"""
from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd

METRICAS = ("AUC", "PR-AUC", "Captura@20", "Fraccion_80")


def desempate(n: int, semilla: int = 42) -> np.ndarray:
    """Vector fijo para desempatar puntajes iguales de forma reproducible."""
    return np.random.default_rng(semilla).random(n)


class Ranking:
    """Un puntaje evaluado sobre un conjunto de filas, con ordenamiento precalculado.

    Args:
        y: etiqueta 0/1.
        score: puntaje (mayor = más probable positivo).
        tb: vector de desempate (mismo largo), por ejemplo ``desempate(n)``.
    """

    def __init__(self, y: np.ndarray, score: np.ndarray, tb: np.ndarray) -> None:
        y = np.asarray(y, dtype=float)
        s = np.asarray(score, dtype=float)
        self.orden = np.lexsort((tb, -s))
        self.y = y[self.orden]
        s_ord = s[self.orden]
        cambio = np.r_[True, s_ord[1:] != s_ord[:-1]]
        self.grupo = np.cumsum(cambio) - 1
        self.n_grupos = int(self.grupo[-1]) + 1

    def metricas(self, w: np.ndarray | None = None) -> np.ndarray:
        """AUC, PR-AUC, Captura@20 y Fracción para 80 %, con pesos de fila ``w`` opcionales.

        Devuelve NaN si no hay positivos o negativos con peso.
        """
        ws = np.ones_like(self.y) if w is None else np.asarray(w, dtype=float)[self.orden]
        wp, wn = ws * self.y, ws * (1.0 - self.y)
        P, N, W = wp.sum(), wn.sum(), ws.sum()
        if P <= 0 or N <= 0:
            return np.full(4, np.nan)
        gp = np.bincount(self.grupo, weights=wp, minlength=self.n_grupos)
        gn = np.bincount(self.grupo, weights=wn, minlength=self.n_grupos)
        cn = np.cumsum(gn)
        cp = np.cumsum(gp)
        auc = float((gp * ((N - cn) + 0.5 * gn)).sum() / (P * N))
        den = cp + cn
        prec = np.divide(cp, den, out=np.zeros_like(cp), where=den > 0)
        ap = float(((gp / P) * prec).sum())
        cum_pos = np.cumsum(wp) / P
        cum_rows = np.cumsum(ws)
        k20 = min(int(np.searchsorted(cum_rows, 0.2 * W)), len(ws) - 1)
        k80 = min(int(np.searchsorted(cum_pos, 0.8)), len(ws) - 1)
        return np.array([auc, ap, float(cum_pos[k20]), float(cum_rows[k80] / W)])


class RankingDosPasos:
    """Brazo C: las cajas de celdas con hueco las atiende la auditoría (primero y sin costo de revisión
    individual) y el modelo ordena solo el resto.

    Args:
        y: etiqueta 0/1.
        score: puntaje del modelo (se ignora en las filas de auditoría).
        tb: vector de desempate.
        auditoria: True en las cajas que cubre la auditoría de cámara (Lista A).
    """

    def __init__(self, y: np.ndarray, score: np.ndarray, tb: np.ndarray, auditoria: np.ndarray) -> None:
        s = np.where(np.asarray(auditoria, dtype=bool), np.inf, np.asarray(score, dtype=float))
        self.orden = np.lexsort((tb, -s))
        self.y = np.asarray(y, dtype=float)[self.orden]
        self.gratis = np.asarray(auditoria, dtype=bool)[self.orden]

    def metricas(self, w: np.ndarray | None = None) -> np.ndarray:
        """Captura@20 y Fracción para 80 % del proceso completo, con el costo medido en cajas de la
        cola del modelo (las cajas auditadas no cuestan) sobre el total de cajas."""
        ws = np.ones_like(self.y) if w is None else np.asarray(w, dtype=float)[self.orden]
        wp = ws * self.y
        P, W = wp.sum(), ws.sum()
        if P <= 0:
            return np.full(2, np.nan)
        cum_pos = np.cumsum(wp) / P
        cum_cost = np.cumsum(ws * (~self.gratis))
        k20 = min(int(np.searchsorted(cum_cost, 0.2 * W)), len(ws) - 1)
        k80 = min(int(np.searchsorted(cum_pos, 0.8)), len(ws) - 1)
        return np.array([float(cum_pos[k20]), float(cum_cost[k80] / W)])


def pesos_bootstrap(seg_codes: np.ndarray, n_boot: int, semilla: int = 42) -> np.ndarray:
    """Pesos por segmento de ``n_boot`` réplicas: matriz (n_boot, n_segmentos) de conteos."""
    n_seg = int(seg_codes.max()) + 1
    rng = np.random.default_rng(semilla)
    return np.stack([np.bincount(rng.integers(0, n_seg, n_seg), minlength=n_seg) for _ in range(n_boot)])


def ic95(valores: np.ndarray, nivel: float = 0.95) -> tuple[float, float]:
    """Intervalo percentil (ignora NaN)."""
    v = np.asarray(valores, dtype=float)
    v = v[~np.isnan(v)]
    a = (1 - nivel) / 2
    return float(np.quantile(v, a)), float(np.quantile(v, 1 - a))


class ConjuntoOOF:
    """Puntajes fuera de fold de varios métodos, con una o más repeticiones, sobre las mismas filas.

    Args:
        y: etiqueta de las filas.
        seg: identificador de segmento de cada fila.
        puntajes: ``{método: [vector_rep1, vector_rep2, ...]}``; cada vector tiene el largo de ``y``.
        semilla: semilla del desempate.
    """

    def __init__(self, y: np.ndarray, seg: Sequence, puntajes: dict[str, list[np.ndarray]], semilla: int = 42) -> None:
        self.y = np.asarray(y)
        codigos, self.segmentos = pd.factorize(np.asarray(seg))
        self.seg_codes = codigos
        self.tb = desempate(len(self.y), semilla)
        self.puntajes = {k: [np.asarray(v, dtype=float) for v in vs] for k, vs in puntajes.items()}
        self._rank: dict[tuple[str, int], Ranking] = {}

    def _r(self, nombre: str, rep: int) -> Ranking:
        clave = (nombre, rep)
        if clave not in self._rank:
            self._rank[clave] = Ranking(self.y, self.puntajes[nombre][rep], self.tb)
        return self._rank[clave]

    def metricas(self, nombre: str, w_seg: np.ndarray | None = None) -> np.ndarray:
        """Métricas promedio entre repeticiones (con pesos de segmento opcionales)."""
        w = None if w_seg is None else w_seg[self.seg_codes]
        return np.nanmean([self._r(nombre, r).metricas(w) for r in range(len(self.puntajes[nombre]))], axis=0)

    def por_repeticion(self, nombre: str) -> pd.DataFrame:
        """Métricas de cada repetición, sin bootstrap."""
        return pd.DataFrame([self._r(nombre, r).metricas() for r in range(len(self.puntajes[nombre]))], columns=list(METRICAS))

    def bootstrap(self, nombres: Sequence[str], n_boot: int = 1000, semilla: int = 42) -> dict[str, np.ndarray]:
        """Matriz (n_boot, 4) de métricas por método, con los mismos pesos para todos (pareado)."""
        pesos = pesos_bootstrap(self.seg_codes, n_boot, semilla)
        return {n: np.array([self.metricas(n, pesos[b]) for b in range(n_boot)]) for n in nombres}


def ece_cuantiles(y: np.ndarray, p: np.ndarray, n_bins: int = 10) -> tuple[float, pd.DataFrame]:
    """Error de calibración esperado con ``n_bins`` cuantiles de la probabilidad (igual que EP2)."""
    b = pd.qcut(pd.Series(p).rank(method="first"), n_bins, labels=False)
    g = pd.DataFrame({"y": y, "p": p, "b": b.to_numpy()}).groupby("b").agg(n=("y", "size"), obs=("y", "mean"), pred=("p", "mean"))
    return float((g["n"] / g["n"].sum() * (g["obs"] - g["pred"]).abs()).sum()), g


def umbral_para_recall(y: np.ndarray, score: np.ndarray, objetivo: float = 0.80) -> float:
    """Mayor umbral con el que ``score >= umbral`` alcanza al menos ``objetivo`` de recall."""
    y = np.asarray(y)
    s = np.asarray(score, dtype=float)
    o = np.argsort(-s, kind="stable")
    cum = np.cumsum(y[o]) / max(y.sum(), 1)
    k = int(np.searchsorted(cum, objetivo))
    return float(s[o][min(k, len(s) - 1)])


def umbral_para_revision(score: np.ndarray, fraccion: float = 0.20) -> float:
    """Umbral tal que se revisa aproximadamente la fracción ``fraccion`` de filas mejor puntuadas."""
    s = np.sort(np.asarray(score, dtype=float))[::-1]
    return float(s[max(int(np.ceil(fraccion * len(s))) - 1, 0)])


def confusion(flag: np.ndarray, y: np.ndarray, w: np.ndarray | None = None) -> dict[str, float]:
    """TP, FP, FN, TN, recall, precisión y porcentaje a revisar (con pesos opcionales)."""
    f = np.asarray(flag, dtype=bool)
    yy = np.asarray(y) == 1
    ww = np.ones(len(yy)) if w is None else np.asarray(w, dtype=float)
    tp, fp = float((ww * (f & yy)).sum()), float((ww * (f & ~yy)).sum())
    fn, tn = float((ww * (~f & yy)).sum()), float((ww * (~f & ~yy)).sum())
    return {
        "TP": tp, "FP": fp, "FN": fn, "TN": tn,
        "recall": tp / max(tp + fn, 1e-12), "precision": tp / max(tp + fp, 1e-12),
        "pct_revisar": (tp + fp) / max(tp + fp + fn + tn, 1e-12),
    }


def f1_accuracy(flag: np.ndarray, y: np.ndarray) -> dict[str, float]:
    """F1 y accuracy de un punto de operación (solo referencia, no deciden nada)."""
    c = confusion(flag, y)
    p, r = c["precision"], c["recall"]
    return {"F1": 2 * p * r / max(p + r, 1e-12), "accuracy": (c["TP"] + c["TN"]) / (c["TP"] + c["TN"] + c["FP"] + c["FN"])}
