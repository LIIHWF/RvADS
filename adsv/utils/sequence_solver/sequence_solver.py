from adsv.utils.types import *
import z3

class Symbol:
    def __init__(self, id_):
        self.id = id_

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other: 'Symbol'):
        return self.id == other.id

    def __str__(self):
        return str(self.id)

    def __repr__(self):
        return repr(self.id)


class SequenceSolver:
    def __init__(self, option_list: List[Set[Symbol]]):
        self.option_list = option_list
        self._solver = None
        self._symbol_var_map = None

    def build(self):
        self._solver = z3.Optimize()
        try:
            all_symbols = set()
            for symbols in self.option_list:
                all_symbols |= symbols
            self._symbol_var_map = []
            for i, option in enumerate(self.option_list):
                self._symbol_var_map.append(dict())
                for j, symbol in enumerate(option):
                    self._symbol_var_map[i][symbol] = z3.Bool(f's[{i}]={symbol}')
            for option in self._symbol_var_map:
                option = option.values()
                self._solver.add(z3.AtMost(*option, 1))
                self._solver.add(z3.AtLeast(*option, 1))
        except Exception as e:
            self._solver = None
            raise e

    def solve(self, neighbors: Union[Mapping[Symbol, Set[Symbol]], Mapping[Symbol, Mapping[Symbol, int]]]) -> Optional[List[Symbol]]:
        if self._solver is None:
            self.build()
        self._solver.push()
        for i in range(1, len(self.option_list)):
            prev_options = self.option_list[i-1]
            next_options = self.option_list[i]
            for p_option in prev_options:
                if p_option not in neighbors:
                    self._solver.add(z3.Not(self._symbol_var_map[i-1][p_option]))
                    continue
                neighbor = neighbors[p_option]
                if isinstance(neighbor, Mapping):
                    for n_option, score in neighbor.items():
                        if n_option in next_options:
                            self._solver.add_soft(self._symbol_var_map[i-1][p_option] == self._symbol_var_map[i][n_option], score)
                    # self._solver.add(z3.Implies(self._symbol_var_map[i - 1][p_option], z3.Or(
                    #     *[self._symbol_var_map[i][n_option] for n_option in neighbor.keys() & next_options])))
                elif isinstance(neighbor, Set) or isinstance(neighbor, FrozenSet):
                    self._solver.add(z3.Implies(self._symbol_var_map[i-1][p_option], z3.Or(*[self._symbol_var_map[i][n_option] for n_option in neighbor & next_options])))
        sat_stat = self._solver.check()
        if sat_stat == z3.unsat:
            return None
        else:
            mdl = self._solver.model()
            self._solver.pop()
            ret = []
            for i in range(len(self.option_list)):
                for symbol, var in self._symbol_var_map[i].items():
                    if mdl[var]:
                        ret.append(symbol)
                        break
            return ret





