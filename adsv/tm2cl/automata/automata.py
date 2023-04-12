from adsv.utils.types import *
import time


class State:
    def __init__(self, _id: int):
        self._id = _id

    @property
    def id(self) -> int:
        return self._id

    def __eq__(self, other: 'State'):
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

    def __str__(self):
        return str(self.id)

    def __repr__(self):
        return repr(self.id)


class Symbol:
    def __init__(self, name: str):
        self._name = name

    @property
    def name(self):
        return self._name

    def __eq__(self, other: 'Symbol'):
        return self.name == other.name

    def __lt__(self, other: 'Symbol'):
        return self.name < other.name

    def __hash__(self):
        return hash(self.name)

    def __str__(self):
        return str(self.name)

    def __repr__(self):
        return str(self.name)


class TranslateCondition:
    def __init__(self, positive_symbols: Set[Symbol]):
        self._positive_symbols = frozenset(positive_symbols)
        self._sorted_symbols = tuple(sorted(self._positive_symbols))

    def __hash__(self):
        return hash(self._sorted_symbols)

    def __eq__(self, other: 'TranslateCondition'):
        return self.sorted_symbols == other.sorted_symbols

    @property
    def positive_symbols(self) -> FrozenSet[Symbol]:
        return self._positive_symbols

    @property
    def sorted_symbols(self) -> Tuple[Symbol, ...]:
        return self._sorted_symbols

    def __str__(self):
        return str(self.positive_symbols)

    def __repr__(self):
        return repr(self.positive_symbols)


class AutomataResult(Enum):
    ACCEPT = 1
    REJECT = 2
    INCONCLUSIVE = 3


class Automata:
    def __init__(self,
                 translations: Mapping[State, Mapping[TranslateCondition, State]],
                 symbols: Set[Symbol],
                 accept_states: Set[State],
                 init_state: Optional[State] = None):
        self._translations: Mapping[State, Mapping[TranslateCondition, State]] = MappingProxyType({
            source: MappingProxyType({
                condition: target for condition, target in condition_map.items()
            }) for source, condition_map in translations.items()
        })
        self._symbols = frozenset(symbols)
        self._accept_states = frozenset(accept_states)
        if init_state is None:
            self._init_state = State(0)
        else:
            self._init_state = init_state

    @property
    def init_state(self) -> State:
        return self._init_state

    @property
    def symbols(self) -> FrozenSet[Symbol]:
        return self._symbols

    @property
    def accept_states(self) -> FrozenSet[State]:
        return self._accept_states

    def next_state(self, current_state: State, positive_symbols: Set[Symbol]) -> Optional[State]:
        translation = TranslateCondition(positive_symbols)
        # if current_state not in self._translations:
        #     return None
        try:
            return self._translations[current_state][translation]
        except KeyError:
            return None

    def check_finite_sequence(self, sequence: Iterable[Set[Symbol]]) -> AutomataResult:
        current_state = self.init_state
        for symbols in sequence:
            current_state = self.next_state(current_state, symbols)
            if current_state is None:
                return AutomataResult.REJECT
        if current_state in self._accept_states:
            return AutomataResult.ACCEPT
        return AutomataResult.INCONCLUSIVE

