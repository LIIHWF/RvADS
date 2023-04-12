from adsv.tm2cl.automata.automata import Automata, State, Symbol, TranslateCondition
import subprocess
from functools import lru_cache


@lru_cache(10)
def run_ltl2fsm(formula: str):
    output = subprocess.run(['third-party/ltl2fsm/ltl2fsm', formula], stdout=subprocess.PIPE)
    lines = output.stdout.decode('utf-8').strip().split('\n')
    output = subprocess.run(['third-party/ltl2fsm/bin/extractalphabet', formula], stdout=subprocess.PIPE)
    return lines, output


def parse_ltl_formula(formula: str):
    lines, output = run_ltl2fsm(formula)
    symbols = set(Symbol(sym) for sym in output.stdout.decode('utf-8').strip().split(',')[-1].strip('()').split('&&'))
    accept_states = set()
    translations = dict()
    for line in lines:
        line = line.strip()
        parts = line.split('\t')
        if len(parts) == 3:
            source, target, condition = parts
            source = State(int(source))
            target = State(int(target))
            condition = condition.strip('()')
            if condition == '<empty>':
                condition = set()
            else:
                condition = set(Symbol(sym) for sym in condition.split('&&'))
            condition = TranslateCondition(condition)
            if source not in translations:
                translations[source] = dict()
            translations[source][condition] = target
        else:
            accept_states.add(State(int(parts[0])))
    automata = Automata(translations, symbols, accept_states)
    return automata
