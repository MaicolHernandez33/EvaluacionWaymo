"""
This is a boilerplate pipeline 'ingesta_waymo'
generated using Kedro 1.5.0
"""

from kedro.pipeline import Node, Pipeline, node  # noqa

from .nodes import (
    cargar_segmentos_waymo,
    construir_target_binario,
    resumen_ingesta_waymo,
)


def create_pipeline(**kwargs) -> Pipeline:
    return Pipeline(
        [
            node(
                func=cargar_segmentos_waymo,
                inputs=["waymo_lidar_box_raw", "params:ingesta_waymo.metadata_segmentos"],
                outputs="waymo_lidar_box_con_metadata",
                name="cargar_segmentos_waymo_node",
            ),
            node(
                func=construir_target_binario,
                inputs="waymo_lidar_box_con_metadata",
                outputs="waymo_con_target",
                name="construir_target_binario_node",
            ),
            node(
                func=resumen_ingesta_waymo,
                inputs="waymo_con_target",
                outputs="resumen_ingesta_waymo",
                name="resumen_ingesta_waymo_node",
            ),
        ]
    )
