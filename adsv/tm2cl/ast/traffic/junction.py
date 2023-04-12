from .position import PositionSet
from adsv.tm2cl.ast.common import Variable, StaticVariable, AstNode
from adsv.utils.types import *
from abc import abstractmethod


class JunctionNode(PositionSet):
    ...


class JunctionVariable(Variable, JunctionNode):
    def __init__(self, name: str):
        self._init_variable(name)

    @property
    def sub_nodes(self) -> Tuple:
        return ()

    def apply_sub_nodes(self) -> 'JunctionVariable':
        return JunctionVariable(self.name)

    def __repr__(self):
        return f'JunctionVariable({self.name})'


class JunctionValue(StaticVariable, JunctionNode):
    def __init__(self, id_: str):
        self._init_static_variable(id_)

    @property
    def sub_nodes(self) -> Tuple:
        return ()

    def apply_sub_nodes(self) -> 'JunctionValue':
        return JunctionValue(self.id)

    def __str__(self):
        return str(self.id)

    def __repr__(self):
        return f'JunctionValue({self.id})'


class JunctionEndpoint(PositionSet):
    ...


class JunctionEndpointVariable(Variable, JunctionEndpoint):
    def _init_junction_endpoint_variable(self, junction_node: 'JunctionNode', name: str):
        self._init_variable(f'{junction_node.char}.{name}')
        self.junction_node = junction_node

    @property
    def sub_nodes(self) -> Tuple['JunctionNode']:
        return self.junction_node,


class JunctionEndpointValue(StaticVariable, JunctionEndpoint):
    def _init_junction_endpoint_value(self, junction_node: 'JunctionNode', id_: str):
        self._init_static_variable(f'{junction_node.char}.{id_}')
        self.junction_node = junction_node
        self.node_order = int(id_)

    @property
    def sub_nodes(self) -> Tuple['JunctionNode']:
        return self.junction_node,


class JunctionEntranceVariable(JunctionEndpointVariable):
    def __init__(self, junction_node: 'JunctionNode', name: str):
        self._init_junction_endpoint_variable(junction_node, name)

    def apply_sub_nodes(self, junction_node: 'JunctionNode') -> 'JunctionEntranceVariable':
        return JunctionEntranceVariable(junction_node, self.name[len(self.junction_node.char)+1:])

    def __repr__(self):
        return f'JunctionEntranceVariable({self.junction_node}, {self.name})'


class JunctionExitVariable(JunctionEndpointVariable):
    def __init__(self, junction_node: 'JunctionNode', name: str):
        self._init_junction_endpoint_variable(junction_node, name)

    def apply_sub_nodes(self, junction_node: 'JunctionNode') -> 'JunctionExitVariable':
        return JunctionExitVariable(junction_node, self.name[len(self.junction_node.char)+1:])

    def __repr__(self):
        return f'JunctionExitVariable({self.junction_node}, {self.name})'


class JunctionEntranceValue(JunctionEndpointValue):
    def __init__(self, junction_node: 'JunctionNode', id_: str):
        self._init_junction_endpoint_value(junction_node, id_)

    def apply_sub_nodes(self, junction_node: 'JunctionNode') -> 'JunctionEntranceValue':
        return JunctionEntranceValue(junction_node, self.id[len(self.junction_node.char)+1:])

    def __str__(self):
        return f'en({self.id})'

    def __repr__(self):
        return f'JunctionEntranceValue({self.junction_node}, {self.id})'


class JunctionExitValue(JunctionEndpointValue):
    def __init__(self, junction_node: 'JunctionNode', id_: str):
        self._init_junction_endpoint_value(junction_node, id_)

    def apply_sub_nodes(self, junction_node: 'JunctionNode') -> 'JunctionEntranceValue':
        return JunctionEntranceValue(junction_node, self.id[len(self.junction_node.char)+1:])
    def __str__(self):
        return f'ex({self.id})'

    def __repr__(self):
        return f'JunctionExitValue({self.junction_node}, {self.id})'


class JunctionEndpointSet(StaticVariable, PositionSet):
    def _init(self, junction_node: 'JunctionNode'):
        if isinstance(junction_node, JunctionVariable):
            super().__init__(f'{junction_node.name}.En')
        elif isinstance(junction_node, JunctionValue):
            super().__init__(f'{junction_node.id}.En')
        self.junction_node = junction_node

    @property
    def sub_nodes(self) -> Tuple['JunctionNode']:
        return self.junction_node,


class JunctionEntranceSet(JunctionEndpointSet):
    def __init__(self, junction_node: 'JunctionNode'):
        self._init(junction_node)

    def apply_sub_nodes(self, junction_node: 'JunctionNode') -> 'JunctionEntranceSet':
        return JunctionEntranceSet(self.junction_node)

    def __repr__(self):
        return f'JunctionEntranceSet({self.junction_node})'


class JunctionExitSet(JunctionEndpointSet):
    def __init__(self, junction_node: 'JunctionNode'):
        self._init(junction_node)

    def apply_sub_nodes(self, junction_node: 'JunctionNode') -> 'JunctionExitSet':
        return JunctionExitSet(junction_node)

    def __repr__(self):
        return f'JunctionExitSet({self.junction_node})'
