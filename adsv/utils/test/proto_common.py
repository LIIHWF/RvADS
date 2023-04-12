from adsv.utils.types import *


def make_copy_by_proto(origin: 'ProtoClass'):
    origin_proto = origin.dump()
    origin_proto_str = origin_proto.SerializeToString()
    new_proto = type(origin_proto)()
    new_proto.ParseFromString(origin_proto_str)
    return type(origin)(new_proto)
