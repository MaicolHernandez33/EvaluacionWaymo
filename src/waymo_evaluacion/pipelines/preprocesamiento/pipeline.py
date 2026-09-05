"""
This is a boilerplate pipeline 'preprocesamiento'
generated using Kedro 1.5.0
"""

from kedro.pipeline import Node, Pipeline, node  # noqa

from .nodes import (
    convertir_nulos_ocultos,
    crear_variables_derivadas,
    eliminar_columnas_sin_varianza,
    eliminar_duplicados_logicos,
    filtrar_valores_imposibles,
    normalizar_categorias,
    resumen_calidad,
)


def create_pipeline(**kwargs) -> Pipeline:
    return Pipeline(
        [
            node(
                func=convertir_nulos_ocultos,
                inputs="detecciones_crudas",
                outputs="detecciones_sin_nulos_ocultos",
                name="convertir_nulos_ocultos_node",
            ),
            node(
                func=normalizar_categorias,
                inputs="detecciones_sin_nulos_ocultos",
                outputs="detecciones_categorias_normalizadas",
                name="normalizar_categorias_node",
            ),
            node(
                func=eliminar_columnas_sin_varianza,
                inputs=[
                    "detecciones_categorias_normalizadas",
                    "params:preprocesamiento.columnas_protegidas",
                ],
                outputs="detecciones_sin_columnas_constantes",
                name="eliminar_columnas_sin_varianza_node",
            ),
            node(
                func=eliminar_duplicados_logicos,
                inputs="detecciones_sin_columnas_constantes",
                outputs="detecciones_sin_duplicados",
                name="eliminar_duplicados_logicos_node",
            ),
            node(
                func=filtrar_valores_imposibles,
                inputs=[
                    "detecciones_sin_duplicados",
                    "params:preprocesamiento.altura_maxima_m",
                    "params:preprocesamiento.velocidad_maxima_mps",
                ],
                outputs="detecciones_sin_valores_imposibles",
                name="filtrar_valores_imposibles_node",
            ),
            node(
                func=crear_variables_derivadas,
                inputs="detecciones_sin_valores_imposibles",
                outputs="detecciones_limpias",
                name="crear_variables_derivadas_node",
            ),
            node(
                func=resumen_calidad,
                inputs=["detecciones_crudas", "detecciones_limpias"],
                outputs="resumen_calidad",
                name="resumen_calidad_node",
            ),
        ]
    )
