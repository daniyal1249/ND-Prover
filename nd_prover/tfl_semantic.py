from .logic import *


def prop_vars(formula):
    match formula:
        case PropVar(name):
            return {name}
        case Falsum():
            return set()
        case Not(inner):
            return prop_vars(inner)
        case And(left, right) | Or(left, right) | Imp(left, right) | Iff(left, right):
            return prop_vars(left) | prop_vars(right)
        case _:
            return set()


def evaluate(formula, assignment):
    match formula:
        case Falsum():
            return False
        case PropVar(name):
            return assignment[name]
        case Not(inner):
            return not evaluate(inner, assignment)
        case And(left, right):
            return evaluate(left, assignment) and evaluate(right, assignment)
        case Or(left, right):
            return evaluate(left, assignment) or evaluate(right, assignment)
        case Imp(left, right):
            return not evaluate(left, assignment) or evaluate(right, assignment)
        case Iff(left, right):
            return evaluate(left, assignment) == evaluate(right, assignment)
        case _:
            return False


def is_valid(premises, conclusion):
    all_vars = set()
    for premise in premises:
        all_vars |= prop_vars(premise)
    all_vars |= prop_vars(conclusion)
    
    if not all_vars:
        empty_assignment = {}
        all_premises_true = True
        for premise in premises:
            if not evaluate(premise, empty_assignment):
                all_premises_true = False
                break
        if all_premises_true:
            return evaluate(conclusion, empty_assignment)
        return True
    
    sorted_vars = sorted(all_vars)
    n = len(sorted_vars)
    
    for i in range(2 ** n):
        assignment = {}
        for j, var in enumerate(sorted_vars):
            assignment[var] = bool(i & (1 << (n - 1 - j)))
        
        all_premises_true = True
        for premise in premises:
            if not evaluate(premise, assignment):
                all_premises_true = False
                break
        
        if all_premises_true:
            conclusion_value = evaluate(conclusion, assignment)
            if not conclusion_value:
                return False
    
    return True
