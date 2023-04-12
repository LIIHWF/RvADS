from adsv.utils.types import *
from adsv.ads_libs.apollo.map.proto import map_pb2
from google.protobuf import text_format


class ApolloMapParser(metaclass=multimeta):
    @overload
    def __init__(self, proto_bytes: bytes):
        self.proto: map_pb2.Map = map_pb2.Map()
        self.proto.ParseFromString(proto_bytes)
        self._lanes = None
        self._signals = None

    @overload
    def __init__(self, proto_text: str):
        self.proto: map_pb2.Map = text_format.Parse(proto_text, map_pb2.Map())

    def dump(self) -> bytes:
        return self.proto.SerializeToString()

    def dumps(self) -> str:
        return str(self.proto)

    def copy(self) -> 'ApolloMapParser':
        map_proto = ApolloMapParser(self.dump())
        return map_proto
