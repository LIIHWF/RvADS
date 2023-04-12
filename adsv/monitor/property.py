from adsv.tm2cl.tactic import *
from adsv.tm2cl.ast.internal_node import *
from adsv.tm2cl.ast import *
from adsv.utils.types import *


class Property:
    def __init__(self, variables: Tuple[Variable, ...], premise: Formula, specification: Formula):
        self._variables = variables
        self._premise = premise
        self._specification = specification

    @property
    def variables(self) -> Tuple[Variable, ...]:
        return self._variables

    @property
    def premise(self) -> Formula:
        return self._premise

    @property
    def specification(self) -> Formula:
        return self._specification

    @cached_property
    def bounded_premise(self) -> Formula:
        def _construct(vars: Tuple[Variable], formula: Formula):
            if len(vars) == 0:
                return formula
            return _construct(vars[:-1], Exist(vars[-1], formula))
        return _construct(self.variables, Eventual(self.premise))

    @cached_property
    def bounded_formula(self) -> Formula:
        def _construct(vars: Tuple[Variable], formula: Formula):
            if len(vars) == 0:
                return formula
            return _construct(vars[:-1], Forall(vars[-1], formula))
        return _construct(self.variables, Always(Implies(self.premise, self.specification)))


