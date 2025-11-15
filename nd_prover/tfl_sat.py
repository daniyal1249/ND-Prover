from .logic import *


def prop_vars(formula):
    match formula:
        case PropVar(s):
            return {s}
        case Bot():
            return set()
        case Not(a):
            return prop_vars(a)
        case And(a, b) | Or(a, b) | Imp(a, b) | Iff(a, b):
            return prop_vars(a) | prop_vars(b)
        case _:
            return set()


def evaluate(formula, model):
    match formula:
        case Bot():
            return False
        case PropVar(s):
            return model[s]
        case Not(a):
            return not evaluate(a, model)
        case And(a, b):
            return evaluate(a, model) and evaluate(b, model)
        case Or(a, b):
            return evaluate(a, model) or evaluate(b, model)
        case Imp(a, b):
            return not evaluate(a, model) or evaluate(b, model)
        case Iff(a, b):
            return evaluate(a, model) == evaluate(b, model)
        case _:
            return False


def is_valid(premises, conclusion):
    all_vars = set()
    for premise in premises:
        all_vars |= prop_vars(premise)
    all_vars |= prop_vars(conclusion)
    
    if not all_vars:
        empty_model = {}
        all_premises_true = True
        for premise in premises:
            if not evaluate(premise, empty_model):
                all_premises_true = False
                break
        if all_premises_true:
            return evaluate(conclusion, empty_model)
        return True
    
    sorted_vars = sorted(all_vars)
    n = len(sorted_vars)
    
    for i in range(2 ** n):
        model = {}
        for j, var in enumerate(sorted_vars):
            model[var] = bool(i & (1 << (n - 1 - j)))
        
        all_premises_true = True
        for premise in premises:
            if not evaluate(premise, model):
                all_premises_true = False
                break
        
        if all_premises_true:
            conclusion_value = evaluate(conclusion, model)
            if not conclusion_value:
                return False

    return True
