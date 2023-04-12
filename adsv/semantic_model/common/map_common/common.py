from enum import Enum
from adsv.semantic_model.common.map_common.proto import map_common_pb2


RJType = Enum('RJType', {name: id_ for name, id_ in map_common_pb2.RJType.items()})
TurnType = Enum('TurnType', {name: id_ for name, id_ in map_common_pb2.TurnType.items()})
