"""
This is a boilerplate pipeline 'ingesta_waymo'
generated using Kedro 1.5.0
"""

from kedro.pipeline import Node, Pipeline, node  # noqa

from .nodes import (
    cargar_segmentos_waymo,
    construir_target_binario,
    crear_variables_waymo,
    filtrar_frames_etiquetados,
    resumen_ingesta_waymo,
)


def create_pipeline(**kwargs) -> Pipeline:
    return Pipeline(
        [
            node(
                func=cargar_segmentos_waymo,
                inputs=[
                    "waymo_lidar_box_raw",
                    "waymo_inventario_segmentos",
                    "params:segmentos_ep2.segmentos_supervisado",
                    "params:segmentos_ep2.segmentos_solo_clustering",
                ],
                outputs="waymo_lidar_box_con_metadata",
                name="cargar_segmentos_waymo_node",
            ),
            node(
                func=crear_variables_waymo,
                inputs="waymo_lidar_box_con_metadata",
                outputs="waymo_con_variables",
                name="crear_variables_waymo_node",
            ),
            node(
                func=construir_target_binario,
                inputs=[
                    "waymo_con_variables",
                    "waymo_asociacion_raw",
                    "params:segmentos_ep2.segmentos_supervisado",
                ],
                outputs="waymo_con_target",
                name="construir_target_binario_node",
            ),
            node(
                func=filtrar_frames_etiquetados,
                inputs="waymo_con_target",
                outputs=["waymo_supervisado", "reporte_filtro_frames"],
                name="filtrar_frames_etiquetados_node",
            ),
            node(
                func=resumen_ingesta_waymo,
                inputs="waymo_con_target",
                outputs="resumen_ingesta_waymo",
                name="resumen_ingesta_waymo_node",
            ),
        ]
    )
