from .logic import *
from .tfl_semantic import is_valid


# Main entry point
def prove(premises, conclusion):
    if not is_valid(premises, conclusion):
        return None
    
    proof = Proof(TFL, premises, conclusion)
    
    formula_to_idx = {}
    for i, premise in enumerate(premises, start=1):
        formula_to_idx[premise] = i
    
    if can_derive_immediately(conclusion, formula_to_idx):
        if not proof.is_complete():
            rule = get_rule_by_name("R")
            conclusion_idx = formula_to_idx[conclusion]
            justification = Justification(rule, (conclusion_idx,))
            proof.add_line(conclusion, justification)
        return proof
    
    memo = {}
    max_depth = 20
    depth = 0
    
    if isinstance(conclusion, And) and conclusion.left == conclusion.right:
        if can_derive_immediately(conclusion.left, formula_to_idx):
            left_idx = formula_to_idx[conclusion.left]
            rule = get_rule_by_name("∧I")
            justification = Justification(rule, (left_idx, left_idx))
            proof.add_line(conclusion, justification)
            if not proof.is_complete():
                rule = get_rule_by_name("R")
                conclusion_idx = get_current_line_index(proof)
                justification = Justification(rule, (conclusion_idx,))
                proof.add_line(conclusion, justification)
            return proof
    
    while depth < max_depth:
        max_iterations = 20
        iteration = 0
        
        while iteration < max_iterations:
            new_formulas = forward_chain_iteration(proof, formula_to_idx, conclusion)
            
            if not new_formulas:
                break
            
            formula_to_idx.update(new_formulas)
            
            if can_derive_immediately(conclusion, formula_to_idx):
                if not proof.is_complete():
                    rule = get_rule_by_name("R")
                    conclusion_idx = formula_to_idx[conclusion]
                    justification = Justification(rule, (conclusion_idx,))
                    proof.add_line(conclusion, justification)
                return proof
            
            iteration += 1
        
        if can_derive_immediately(conclusion, formula_to_idx):
            if not proof.is_complete():
                rule = get_rule_by_name("R")
                conclusion_idx = formula_to_idx[conclusion]
                justification = Justification(rule, (conclusion_idx,))
                proof.add_line(conclusion, justification)
            return proof
        
        if backward_chain(proof, conclusion, formula_to_idx, depth, max_depth, memo):
            if can_derive_immediately(conclusion, formula_to_idx):
                if not proof.is_complete():
                    rule = get_rule_by_name("R")
                    conclusion_idx = formula_to_idx[conclusion]
                    justification = Justification(rule, (conclusion_idx,))
                    proof.add_line(conclusion, justification)
                return proof
        
        depth += 1
    
    if proof.is_complete():
        return proof
    
    return None


# Formula utilities
def is_compound(formula):
    match formula:
        case PropVar() | Falsum():
            return False
        case _:
            return True


def get_main_connective(formula):
    match formula:
        case And():
            return And
        case Or():
            return Or
        case Imp():
            return Imp
        case Iff():
            return Iff
        case Not():
            return Not
        case PropVar():
            return PropVar
        case Falsum():
            return Falsum
        case _:
            return None


# Availability checks
def can_derive_immediately(goal, available):
    return goal in available


def can_derive_via_context(proof, goal, formula_to_idx):
    if goal in formula_to_idx:
        return True
    return find_formula_in_context_and_add(proof, goal, formula_to_idx)


# Proof structure utilities
def get_current_line_index(proof):
    return proof.proof.idx[1]


def find_subproof_by_start_idx(subproof, target_idx):
    if subproof.assumption:
        if (subproof.seq and subproof.seq[0].is_line() and
                subproof.seq[0].idx == target_idx):
            return subproof
    for obj in subproof.seq:
        if obj.is_subproof():
            result = find_subproof_by_start_idx(obj, target_idx)
            if result is not None:
                return result
    return None


def find_deepest_active_subproof(proof):
    current = proof.proof
    while current.seq and current.seq[-1].is_subproof():
        current = current.seq[-1]
    return current


def find_formula_in_context_and_add(proof, formula, formula_to_idx):
    if formula in formula_to_idx:
        return True
    
    deepest_subproof = find_deepest_active_subproof(proof)
    scope = deepest_subproof.context + deepest_subproof.seq
    
    for obj in scope:
        if obj.is_line() and obj.formula == formula:
            rule = get_rule_by_name("R")
            justification = Justification(rule, (obj.idx,))
            proof.add_line(formula, justification)
            new_idx = get_current_line_index(proof)
            formula_to_idx[formula] = new_idx
            return True
    
    return False


# Subproof management
def cleanup_subproof_from_index(proof, assumption_idx):
    while get_current_line_index(proof) >= assumption_idx:
        try:
            proof.delete_line()
        except:
            break


def ensure_conclusion_in_subproof(proof, assumption_idx, goal, goal_idx):
    active_subproof = find_subproof_by_start_idx(proof.proof, assumption_idx)
    if active_subproof is not None:
        subproof_conclusion = active_subproof.conclusion
        if subproof_conclusion != goal:
            rule = get_rule_by_name("R")
            justification = Justification(rule, (goal_idx,))
            proof.add_line(goal, justification)
    else:
        current_idx = get_current_line_index(proof)
        if current_idx != goal_idx:
            rule = get_rule_by_name("R")
            justification = Justification(rule, (goal_idx,))
            proof.add_line(goal, justification)


def forward_chain_in_subproof(proof, formula_to_idx, goal=None, max_iterations=20):
    iteration = 0
    while iteration < max_iterations:
        new_formulas = forward_chain_iteration(proof, formula_to_idx, goal)
        formula_to_idx.update(new_formulas)
        
        if goal is not None and can_derive_immediately(goal, formula_to_idx):
            return True
        
        if not new_formulas:
            break
        
        iteration += 1
    return goal is not None and can_derive_immediately(goal, formula_to_idx)


def find_nested_subproof_idx(proof, assumption_idx):
    deepest_subproof = find_subproof_by_start_idx(proof.proof, assumption_idx)
    if deepest_subproof is None:
        return None
    nested_subproof = deepest_subproof
    while nested_subproof.seq and nested_subproof.seq[-1].is_subproof():
        nested_subproof = nested_subproof.seq[-1]
    return nested_subproof.idx


def attempt_derive_in_subproof(
        proof, assumption, formula_to_idx, goal, depth, max_depth, memo):
    proof.begin_subproof(assumption)
    assumption_idx = get_current_line_index(proof)
    
    subproof_formula_to_idx = formula_to_idx.copy()
    subproof_formula_to_idx[assumption] = assumption_idx
    
    if not forward_chain_in_subproof(proof, subproof_formula_to_idx, goal):
        if backward_chain(
                proof, goal, subproof_formula_to_idx, depth + 1, max_depth, memo):
            if not can_derive_immediately(goal, subproof_formula_to_idx):
                cleanup_subproof_from_index(proof, assumption_idx)
                return None
        else:
            cleanup_subproof_from_index(proof, assumption_idx)
            return None
    
    if not can_derive_immediately(goal, subproof_formula_to_idx):
        cleanup_subproof_from_index(proof, assumption_idx)
        return None
    
    return subproof_formula_to_idx, assumption_idx


# Rule utilities
def get_rule_by_name(name):
    for rule in Rules.rules:
        if rule.name == name:
            return rule
    return None


# Elimination rules
def apply_and_elimination(proof, formula, formula_to_idx):
    if not isinstance(formula, And):
        return []
    
    if formula not in formula_to_idx:
        return []
    
    results = []
    premise_idx = formula_to_idx[formula]
    rule = get_rule_by_name("∧E")
    
    if formula.left not in formula_to_idx:
        left_justification = Justification(rule, (premise_idx,))
        proof.add_line(formula.left, left_justification)
        left_idx = get_current_line_index(proof)
        results.append((formula.left, left_idx))
    
    if formula.right not in formula_to_idx:
        right_justification = Justification(rule, (premise_idx,))
        proof.add_line(formula.right, right_justification)
        right_idx = get_current_line_index(proof)
        results.append((formula.right, right_idx))
    
    return results


def apply_imp_elimination(proof, formula, formula_to_idx):
    if not isinstance(formula, Imp):
        return []
    
    if formula not in formula_to_idx:
        return []
    
    if formula.left not in formula_to_idx:
        return []
    
    if formula.right in formula_to_idx:
        return []
    
    premise_idx = formula_to_idx[formula]
    left_idx = formula_to_idx[formula.left]
    
    rule = get_rule_by_name("→E")
    justification = Justification(rule, (premise_idx, left_idx))
    proof.add_line(formula.right, justification)
    new_idx = get_current_line_index(proof)
    
    return [(formula.right, new_idx)]


def apply_iff_elimination(proof, formula, formula_to_idx):
    if not isinstance(formula, Iff):
        return []
    
    if formula not in formula_to_idx:
        return []
    
    premise_idx = formula_to_idx[formula]
    results = []
    rule = get_rule_by_name("↔E")
    
    if formula.left in formula_to_idx and formula.right not in formula_to_idx:
        left_idx = formula_to_idx[formula.left]
        justification = Justification(rule, (premise_idx, left_idx))
        proof.add_line(formula.right, justification)
        new_idx = get_current_line_index(proof)
        results.append((formula.right, new_idx))
    
    elif formula.left in formula_to_idx and formula.right in formula_to_idx:
        right_idx = formula_to_idx[formula.right]
        results.append((formula.right, right_idx))
    
    if formula.right in formula_to_idx and formula.left not in formula_to_idx:
        right_idx = formula_to_idx[formula.right]
        justification = Justification(rule, (premise_idx, right_idx))
        proof.add_line(formula.left, justification)
        new_idx = get_current_line_index(proof)
        results.append((formula.left, new_idx))
    
    elif (formula.right in formula_to_idx and formula.left in formula_to_idx and
            formula.left != formula.right):
        left_idx = formula_to_idx[formula.left]
        results.append((formula.left, left_idx))
    
    return results


def apply_not_elimination(proof, formula, formula_to_idx):
    if not isinstance(formula, Not):
        return []
    
    if formula not in formula_to_idx:
        return []
    
    if formula.inner not in formula_to_idx:
        return []
    
    if Falsum() in formula_to_idx:
        return []
    
    not_idx = formula_to_idx[formula]
    inner_idx = formula_to_idx[formula.inner]
    
    rule = get_rule_by_name("¬E")
    justification = Justification(rule, (not_idx, inner_idx))
    proof.add_line(Falsum(), justification)
    new_idx = get_current_line_index(proof)
    
    return [(Falsum(), new_idx)]


def apply_dne(proof, formula, formula_to_idx):
    if not isinstance(formula, Not):
        return []
    
    if not isinstance(formula.inner, Not):
        return []
    
    if formula not in formula_to_idx:
        return []
    
    if formula.inner.inner in formula_to_idx:
        return []
    
    premise_idx = formula_to_idx[formula]
    
    rule = get_rule_by_name("DNE")
    justification = Justification(rule, (premise_idx,))
    proof.add_line(formula.inner.inner, justification)
    new_idx = get_current_line_index(proof)
    
    return [(formula.inner.inner, new_idx)]


def apply_demorgan(proof, formula, formula_to_idx):
    if formula not in formula_to_idx:
        return []
    
    premise_idx = formula_to_idx[formula]
    rule = get_rule_by_name("DeM")
    results = []
    
    match formula:
        case Not(Or(a, b)):
            result_formula = And(Not(a), Not(b))
            if result_formula not in formula_to_idx:
                justification = Justification(rule, (premise_idx,))
                proof.add_line(result_formula, justification)
                new_idx = get_current_line_index(proof)
                results.append((result_formula, new_idx))
        
        case And(Not(a), Not(b)):
            result_formula = Not(Or(a, b))
            if result_formula not in formula_to_idx:
                justification = Justification(rule, (premise_idx,))
                proof.add_line(result_formula, justification)
                new_idx = get_current_line_index(proof)
                results.append((result_formula, new_idx))
        
        case Not(And(a, b)):
            result_formula = Or(Not(a), Not(b))
            if result_formula not in formula_to_idx:
                justification = Justification(rule, (premise_idx,))
                proof.add_line(result_formula, justification)
                new_idx = get_current_line_index(proof)
                results.append((result_formula, new_idx))
        
        case Or(Not(a), Not(b)):
            result_formula = Not(And(a, b))
            if result_formula not in formula_to_idx:
                justification = Justification(rule, (premise_idx,))
                proof.add_line(result_formula, justification)
                new_idx = get_current_line_index(proof)
                results.append((result_formula, new_idx))
        
        case _:
            pass
    
    return results


def apply_mt(proof, formula, formula_to_idx):
    if not isinstance(formula, Imp):
        return []
    
    if formula not in formula_to_idx:
        return []
    
    not_right = Not(formula.right)
    if not_right not in formula_to_idx:
        return []
    
    result_formula = Not(formula.left)
    if result_formula in formula_to_idx:
        return []
    
    premise_idx = formula_to_idx[formula]
    not_right_idx = formula_to_idx[not_right]
    
    rule = get_rule_by_name("MT")
    justification = Justification(rule, (premise_idx, not_right_idx))
    proof.add_line(result_formula, justification)
    new_idx = get_current_line_index(proof)
    
    return [(result_formula, new_idx)]


def apply_ds(proof, formula, formula_to_idx):
    if not isinstance(formula, Or):
        return []
    
    if formula not in formula_to_idx:
        return []
    
    premise_idx = formula_to_idx[formula]
    rule = get_rule_by_name("DS")
    results = []
    
    not_left = Not(formula.left)
    if not_left in formula_to_idx and formula.right not in formula_to_idx:
        not_left_idx = formula_to_idx[not_left]
        justification = Justification(rule, (premise_idx, not_left_idx))
        proof.add_line(formula.right, justification)
        new_idx = get_current_line_index(proof)
        results.append((formula.right, new_idx))
    
    not_right = Not(formula.right)
    if not_right in formula_to_idx and formula.left not in formula_to_idx:
        not_right_idx = formula_to_idx[not_right]
        justification = Justification(rule, (premise_idx, not_right_idx))
        proof.add_line(formula.left, justification)
        new_idx = get_current_line_index(proof)
        results.append((formula.left, new_idx))
    
    return results


# Or elimination
def attempt_derive_in_or_subproof(proof, assumption, formula_to_idx, goal, memo):
    proof.begin_subproof(assumption)
    assumption_idx = get_current_line_index(proof)
    subproof_formula_to_idx = formula_to_idx.copy()
    subproof_formula_to_idx[assumption] = assumption_idx
    
    goal_derived = forward_chain_in_subproof(proof, subproof_formula_to_idx, goal)
    
    if not goal_derived:
        if not backward_chain(proof, goal, subproof_formula_to_idx, 0, 3, memo):
            cleanup_subproof_from_index(proof, assumption_idx)
            return None
    
    if not can_derive_immediately(goal, subproof_formula_to_idx):
        cleanup_subproof_from_index(proof, assumption_idx)
        return None
    
    goal_idx = subproof_formula_to_idx[goal]
    ensure_conclusion_in_subproof(proof, assumption_idx, goal, goal_idx)
    
    subproof_ref = find_subproof_by_start_idx(proof.proof, assumption_idx)
    if subproof_ref is None:
        cleanup_subproof_from_index(proof, assumption_idx)
        return None
    
    return subproof_ref


def complete_or_elimination(proof, premise_idx, subproof1_ref, subproof2_ref, goal):
    rule = get_rule_by_name("∨E")
    justification = Justification(
        rule, (premise_idx, subproof1_ref.idx, subproof2_ref.idx))
    proof.add_line(goal, justification)
    new_idx = get_current_line_index(proof)
    return new_idx


def apply_or_elimination(proof, disjunction, formula_to_idx, goal=None, memo=None):
    if not isinstance(disjunction, Or):
        return []
    
    if disjunction not in formula_to_idx:
        return []
    
    if goal is None:
        return []
    
    if memo is None:
        memo = {}
    
    premise_idx = formula_to_idx[disjunction]
    
    subproof1_assumption_idx = None
    subproof2_assumption_idx = None
    
    try:
        subproof1_ref = attempt_derive_in_or_subproof(
            proof, disjunction.left, formula_to_idx, goal, memo)
        if subproof1_ref is None:
            return []
        subproof1_assumption_idx = subproof1_ref.idx[0]
        
        subproof2_ref = attempt_derive_in_or_subproof(
            proof, disjunction.right, formula_to_idx, goal, memo)
        if subproof2_ref is None:
            cleanup_subproof_from_index(proof, subproof1_assumption_idx)
            return []
        subproof2_assumption_idx = subproof2_ref.idx[0]
        
        new_idx = complete_or_elimination(
            proof, premise_idx, subproof1_ref, subproof2_ref, goal)
        
        return [(goal, new_idx)]
    except:
        if subproof2_assumption_idx is not None:
            cleanup_subproof_from_index(proof, subproof2_assumption_idx)
        if subproof1_assumption_idx is not None:
            cleanup_subproof_from_index(proof, subproof1_assumption_idx)
        return []


# Forward chaining
def forward_chain_iteration(proof, formula_to_idx, goal=None):
    new_formulas = {}
    formulas_to_try = list(formula_to_idx.keys())
    
    skip_and_elimination = False
    if goal is not None and isinstance(goal, And) and goal.left == goal.right:
        if can_derive_immediately(goal.left, formula_to_idx):
            skip_and_elimination = True
    
    for formula in formulas_to_try:
        if skip_and_elimination and isinstance(formula, And) and formula == goal.left:
            continue
        
        results = apply_and_elimination(proof, formula, formula_to_idx)
        for result_formula, result_idx in results:
            if (result_formula not in formula_to_idx and
                    result_formula not in new_formulas):
                new_formulas[result_formula] = result_idx
                if goal is not None and result_formula == goal:
                    return new_formulas
        
        results = apply_imp_elimination(proof, formula, formula_to_idx)
        for result_formula, result_idx in results:
            if (result_formula not in formula_to_idx and
                    result_formula not in new_formulas):
                new_formulas[result_formula] = result_idx
                if goal is not None and result_formula == goal:
                    return new_formulas
        
        results = apply_iff_elimination(proof, formula, formula_to_idx)
        for result_formula, result_idx in results:
            if (result_formula not in formula_to_idx and
                    result_formula not in new_formulas):
                new_formulas[result_formula] = result_idx
                if goal is not None and result_formula == goal:
                    return new_formulas
        
        results = apply_not_elimination(proof, formula, formula_to_idx)
        for result_formula, result_idx in results:
            if (result_formula not in formula_to_idx and
                    result_formula not in new_formulas):
                new_formulas[result_formula] = result_idx
                if goal is not None and result_formula == goal:
                    return new_formulas
        
        results = apply_dne(proof, formula, formula_to_idx)
        for result_formula, result_idx in results:
            if (result_formula not in formula_to_idx and
                    result_formula not in new_formulas):
                new_formulas[result_formula] = result_idx
                if goal is not None and result_formula == goal:
                    return new_formulas
        
        results = apply_demorgan(proof, formula, formula_to_idx)
        for result_formula, result_idx in results:
            if (result_formula not in formula_to_idx and
                    result_formula not in new_formulas):
                new_formulas[result_formula] = result_idx
                if goal is not None and result_formula == goal:
                    return new_formulas
        
        results = apply_mt(proof, formula, formula_to_idx)
        for result_formula, result_idx in results:
            if (result_formula not in formula_to_idx and
                    result_formula not in new_formulas):
                new_formulas[result_formula] = result_idx
                if goal is not None and result_formula == goal:
                    return new_formulas
        
        results = apply_ds(proof, formula, formula_to_idx)
        for result_formula, result_idx in results:
            if (result_formula not in formula_to_idx and
                    result_formula not in new_formulas):
                new_formulas[result_formula] = result_idx
                if goal is not None and result_formula == goal:
                    return new_formulas
    
    return new_formulas


# Introduction rules
def try_and_introduction(proof, goal, formula_to_idx, depth=0, max_depth=10):
    if not isinstance(goal, And):
        return None
    
    if depth >= max_depth:
        return None
    
    if goal.left not in formula_to_idx:
        if not find_formula_in_context_and_add(proof, goal.left, formula_to_idx):
            return None
    
    if goal.right not in formula_to_idx:
        if not find_formula_in_context_and_add(proof, goal.right, formula_to_idx):
            return None
    
    left_idx = formula_to_idx[goal.left]
    right_idx = formula_to_idx[goal.right]
    
    rule = get_rule_by_name("∧I")
    justification = Justification(rule, (left_idx, right_idx))
    proof.add_line(goal, justification)
    new_idx = get_current_line_index(proof)
    
    return new_idx


def try_or_introduction(proof, goal, formula_to_idx, depth=0, max_depth=10):
    if not isinstance(goal, Or):
        return None
    
    if depth >= max_depth:
        return None
    
    rule = get_rule_by_name("∨I")
    
    if goal.left in formula_to_idx:
        left_idx = formula_to_idx[goal.left]
        justification = Justification(rule, (left_idx,))
        proof.add_line(goal, justification)
        new_idx = get_current_line_index(proof)
        return new_idx
    
    if goal.right in formula_to_idx:
        right_idx = formula_to_idx[goal.right]
        justification = Justification(rule, (right_idx,))
        proof.add_line(goal, justification)
        new_idx = get_current_line_index(proof)
        return new_idx
    
    return None


def try_imp_introduction(proof, goal, formula_to_idx, depth=0, max_depth=10):
    if not isinstance(goal, Imp):
        return None
    
    if depth >= max_depth:
        return None
    
    proof.begin_subproof(goal.left)
    subproof_assumption_idx = get_current_line_index(proof)
    
    subproof_formula_to_idx = formula_to_idx.copy()
    subproof_formula_to_idx[goal.left] = subproof_assumption_idx
    
    if not forward_chain_in_subproof(proof, subproof_formula_to_idx, goal.right):
        cleanup_subproof_from_index(proof, subproof_assumption_idx)
        return None
    
    if not can_derive_immediately(goal.right, subproof_formula_to_idx):
        cleanup_subproof_from_index(proof, subproof_assumption_idx)
        return None
    
    right_idx = subproof_formula_to_idx[goal.right]
    final_idx = get_current_line_index(proof)
    
    if final_idx != right_idx:
        rule = get_rule_by_name("R")
        justification = Justification(rule, (right_idx,))
        proof.add_line(goal.right, justification)
    
    rule = get_rule_by_name("→I")
    subproof_idx_tuple = find_nested_subproof_idx(proof, subproof_assumption_idx)
    if subproof_idx_tuple is None:
        cleanup_subproof_from_index(proof, subproof_assumption_idx)
        return None
    justification = Justification(rule, (subproof_idx_tuple,))
    proof.end_subproof(goal, justification)
    new_idx = get_current_line_index(proof)
    
    return new_idx


def try_not_introduction(proof, goal, formula_to_idx, depth=0, max_depth=10):
    if not isinstance(goal, Not):
        return None
    
    if depth >= max_depth:
        return None
    
    proof.begin_subproof(goal.inner)
    subproof_assumption_idx = get_current_line_index(proof)
    
    subproof_formula_to_idx = formula_to_idx.copy()
    subproof_formula_to_idx[goal.inner] = subproof_assumption_idx
    
    if not forward_chain_in_subproof(proof, subproof_formula_to_idx, Falsum()):
        cleanup_subproof_from_index(proof, subproof_assumption_idx)
        return None
    
    if not can_derive_immediately(Falsum(), subproof_formula_to_idx):
        cleanup_subproof_from_index(proof, subproof_assumption_idx)
        return None
    
    falsum_idx = subproof_formula_to_idx[Falsum()]
    current_idx = get_current_line_index(proof)
    
    if current_idx != falsum_idx:
        rule = get_rule_by_name("R")
        justification = Justification(rule, (falsum_idx,))
        proof.add_line(Falsum(), justification)
    
    rule = get_rule_by_name("¬I")
    subproof_idx_tuple = find_nested_subproof_idx(proof, subproof_assumption_idx)
    if subproof_idx_tuple is None:
        cleanup_subproof_from_index(proof, subproof_assumption_idx)
        return None
    justification = Justification(rule, (subproof_idx_tuple,))
    proof.end_subproof(goal, justification)
    new_idx = get_current_line_index(proof)
    
    return new_idx


def try_indirect_proof(proof, goal, formula_to_idx, depth=0, max_depth=10):
    if depth >= max_depth:
        return None
    
    if can_derive_immediately(goal, formula_to_idx):
        return None
    
    assumption = Not(goal)
    proof.begin_subproof(assumption)
    subproof_assumption_idx = get_current_line_index(proof)
    
    subproof_formula_to_idx = formula_to_idx.copy()
    subproof_formula_to_idx[assumption] = subproof_assumption_idx
    
    max_iterations = 20
    iteration = 0
    
    while iteration < max_iterations:
        new_formulas = forward_chain_iteration(proof, subproof_formula_to_idx, Falsum())
        subproof_formula_to_idx.update(new_formulas)
        
        if can_derive_immediately(Falsum(), subproof_formula_to_idx):
            break
        
        if not new_formulas:
            break
        
        iteration += 1
    
    if not can_derive_immediately(Falsum(), subproof_formula_to_idx):
        while get_current_line_index(proof) >= subproof_assumption_idx:
            try:
                proof.delete_line()
            except:
                break
        return None
    
    falsum_idx = subproof_formula_to_idx[Falsum()]
    current_idx = get_current_line_index(proof)
    
    if current_idx != falsum_idx:
        rule = get_rule_by_name("R")
        justification = Justification(rule, (falsum_idx,))
        proof.add_line(Falsum(), justification)
    
    rule = get_rule_by_name("IP")
    subproof_idx_tuple = find_nested_subproof_idx(proof, subproof_assumption_idx)
    if subproof_idx_tuple is None:
        cleanup_subproof_from_index(proof, subproof_assumption_idx)
        return None
    justification = Justification(rule, (subproof_idx_tuple,))
    proof.end_subproof(goal, justification)
    new_idx = get_current_line_index(proof)
    
    return new_idx


# Backward chaining handlers
def backward_chain_and(proof, goal, formula_to_idx, depth, max_depth, memo, goal_key):
    left, right = goal.left, goal.right
    
    if left == right and can_derive_immediately(left, formula_to_idx):
        left_idx = formula_to_idx[left]
        rule = get_rule_by_name("∧I")
        justification = Justification(rule, (left_idx, left_idx))
        proof.add_line(goal, justification)
        new_idx = get_current_line_index(proof)
        formula_to_idx[goal] = new_idx
        memo[goal_key] = True
        return True
    
    if can_derive_immediately(goal, formula_to_idx):
        memo[goal_key] = True
        return True
    
    left_available = can_derive_via_context(proof, left, formula_to_idx)
    right_available = can_derive_via_context(proof, right, formula_to_idx)
    
    if not left_available:
        if backward_chain(proof, left, formula_to_idx, depth + 1, max_depth, memo):
            left_available = can_derive_via_context(proof, left, formula_to_idx)
    
    if not right_available:
        if backward_chain(proof, right, formula_to_idx, depth + 1, max_depth, memo):
            right_available = can_derive_via_context(proof, right, formula_to_idx)
    
    if left_available and right_available:
        idx = try_and_introduction(proof, goal, formula_to_idx, depth, max_depth)
        if idx is not None:
            formula_to_idx[goal] = idx
            memo[goal_key] = True
            return True
    
    return False


def backward_chain_or(proof, goal, formula_to_idx, depth, max_depth, memo, goal_key):
    left, right = goal.left, goal.right
    
    if backward_chain(proof, left, formula_to_idx, depth + 1, max_depth, memo):
        if can_derive_immediately(left, formula_to_idx):
            idx = try_or_introduction(proof, goal, formula_to_idx, depth, max_depth)
            if idx is not None:
                formula_to_idx[goal] = idx
                memo[goal_key] = True
                return True
    
    if backward_chain(proof, right, formula_to_idx, depth + 1, max_depth, memo):
        if can_derive_immediately(right, formula_to_idx):
            idx = try_or_introduction(proof, goal, formula_to_idx, depth, max_depth)
            if idx is not None:
                formula_to_idx[goal] = idx
                memo[goal_key] = True
                return True
    
    for available_formula in formula_to_idx.keys():
        if isinstance(available_formula, Or) and available_formula != goal:
            results = apply_or_elimination(
                proof, available_formula, formula_to_idx, goal, memo)
            for result_formula, result_idx in results:
                if result_formula == goal:
                    formula_to_idx[goal] = result_idx
                    memo[goal_key] = True
                    return True
    
    return False


def backward_chain_imp(proof, goal, formula_to_idx, depth, max_depth, memo, goal_key):
    left, right = goal.left, goal.right
    
    proof.begin_subproof(left)
    subproof_assumption_idx = get_current_line_index(proof)
    
    subproof_formula_to_idx = formula_to_idx.copy()
    subproof_formula_to_idx[left] = subproof_assumption_idx
    
    if not forward_chain_in_subproof(proof, subproof_formula_to_idx, right):
        if backward_chain(
                proof, right, subproof_formula_to_idx, depth + 1, max_depth, memo):
            if not can_derive_immediately(right, subproof_formula_to_idx):
                cleanup_subproof_from_index(proof, subproof_assumption_idx)
                memo[goal_key] = False
                return False
        else:
            cleanup_subproof_from_index(proof, subproof_assumption_idx)
            memo[goal_key] = False
            return False
    
    if backward_chain(
            proof, right, subproof_formula_to_idx, depth + 1, max_depth, memo):
        if not can_derive_immediately(right, subproof_formula_to_idx):
            cleanup_subproof_from_index(proof, subproof_assumption_idx)
            memo[goal_key] = False
            return False
        
        right_idx = subproof_formula_to_idx[right]
        ensure_conclusion_in_subproof(proof, subproof_assumption_idx, right, right_idx)
        
        rule = get_rule_by_name("→I")
        final_idx = get_current_line_index(proof)
        subproof_idx_tuple = (subproof_assumption_idx, final_idx)
        justification = Justification(rule, (subproof_idx_tuple,))
        proof.end_subproof(goal, justification)
        
        new_idx = get_current_line_index(proof)
        formula_to_idx[goal] = new_idx
        memo[goal_key] = True
        return True
    
    cleanup_subproof_from_index(proof, subproof_assumption_idx)
    return False


def backward_chain_iff(proof, goal, formula_to_idx, depth, max_depth, memo, goal_key):
    left, right = goal.left, goal.right
    
    proof.begin_subproof(left)
    subproof1_assumption_idx = get_current_line_index(proof)
    
    subproof1_formula_to_idx = formula_to_idx.copy()
    subproof1_formula_to_idx[left] = subproof1_assumption_idx
    
    if not forward_chain_in_subproof(proof, subproof1_formula_to_idx, right):
        if backward_chain(
                proof, right, subproof1_formula_to_idx, depth + 1, max_depth, memo):
            if not can_derive_immediately(right, subproof1_formula_to_idx):
                cleanup_subproof_from_index(proof, subproof1_assumption_idx)
                memo[goal_key] = False
                return False
        else:
            cleanup_subproof_from_index(proof, subproof1_assumption_idx)
            memo[goal_key] = False
            return False
    
    if backward_chain(
            proof, right, subproof1_formula_to_idx, depth + 1, max_depth, memo):
        if not can_derive_immediately(right, subproof1_formula_to_idx):
            cleanup_subproof_from_index(proof, subproof1_assumption_idx)
            memo[goal_key] = False
            return False
        
        right_idx = subproof1_formula_to_idx[right]
        ensure_conclusion_in_subproof(proof, subproof1_assumption_idx, right, right_idx)
        
        proof.end_and_begin_subproof(right)
        subproof2_assumption_idx = get_current_line_index(proof)
        
        subproof1_ref = find_subproof_by_start_idx(proof.proof, subproof1_assumption_idx)
        if subproof1_ref is None:
            cleanup_subproof_from_index(proof, subproof2_assumption_idx)
            cleanup_subproof_from_index(proof, subproof1_assumption_idx)
            memo[goal_key] = False
            return False
        subproof1_idx = subproof1_ref.idx
        
        subproof2_formula_to_idx = formula_to_idx.copy()
        subproof2_formula_to_idx[right] = subproof2_assumption_idx
        
        if not forward_chain_in_subproof(proof, subproof2_formula_to_idx, left):
            if backward_chain(
                    proof, left, subproof2_formula_to_idx, depth + 1, max_depth, memo):
                if not can_derive_immediately(left, subproof2_formula_to_idx):
                    cleanup_subproof_from_index(proof, subproof2_assumption_idx)
                    memo[goal_key] = False
                    return False
            else:
                cleanup_subproof_from_index(proof, subproof2_assumption_idx)
                memo[goal_key] = False
                return False
        
        if backward_chain(
                proof, left, subproof2_formula_to_idx, depth + 1, max_depth, memo):
            if not can_derive_immediately(left, subproof2_formula_to_idx):
                cleanup_subproof_from_index(proof, subproof2_assumption_idx)
                memo[goal_key] = False
                return False
            
            left_idx = subproof2_formula_to_idx[left]
            ensure_conclusion_in_subproof(proof, subproof2_assumption_idx, left, left_idx)
            
            subproof2_ref = find_subproof_by_start_idx(proof.proof, subproof2_assumption_idx)
            if subproof2_ref is None:
                cleanup_subproof_from_index(proof, subproof2_assumption_idx)
                memo[goal_key] = False
                return False
            
            rule = get_rule_by_name("↔I")
            justification = Justification(rule, (subproof1_idx, subproof2_ref.idx))
            proof.end_subproof(goal, justification)
            new_idx = get_current_line_index(proof)
            
            formula_to_idx[goal] = new_idx
            memo[goal_key] = True
            return True
        else:
            cleanup_subproof_from_index(proof, subproof2_assumption_idx)
    else:
        cleanup_subproof_from_index(proof, subproof1_assumption_idx)
    
    return False


def backward_chain_atomic(proof, goal, formula_to_idx, depth, max_depth, memo, goal_key):
    for available_formula in list(formula_to_idx.keys()):
        if isinstance(available_formula, Imp) and available_formula.right == goal:
            antecedent = available_formula.left
            if backward_chain(
                    proof, antecedent, formula_to_idx, depth + 1, max_depth, memo):
                if can_derive_immediately(antecedent, formula_to_idx):
                    results = apply_imp_elimination(
                        proof, available_formula, formula_to_idx)
                    for result_formula, result_idx in results:
                        if result_formula == goal:
                            formula_to_idx[goal] = result_idx
                            memo[goal_key] = True
                            return True
    return False


def backward_chain_not(proof, goal, formula_to_idx, depth, max_depth, memo, goal_key):
    inner = goal.inner
    
    proof.begin_subproof(inner)
    subproof_assumption_idx = get_current_line_index(proof)
    
    subproof_formula_to_idx = formula_to_idx.copy()
    subproof_formula_to_idx[inner] = subproof_assumption_idx
    
    if not forward_chain_in_subproof(proof, subproof_formula_to_idx, Falsum()):
        if backward_chain(
                proof, Falsum(), subproof_formula_to_idx, depth + 1, max_depth, memo):
            if not can_derive_immediately(Falsum(), subproof_formula_to_idx):
                cleanup_subproof_from_index(proof, subproof_assumption_idx)
                memo[goal_key] = False
                return False
        else:
            cleanup_subproof_from_index(proof, subproof_assumption_idx)
            memo[goal_key] = False
            return False
    
    if backward_chain(
            proof, Falsum(), subproof_formula_to_idx, depth + 1, max_depth, memo):
        if not can_derive_immediately(Falsum(), subproof_formula_to_idx):
            cleanup_subproof_from_index(proof, subproof_assumption_idx)
            memo[goal_key] = False
            return False
        
        falsum_idx = subproof_formula_to_idx[Falsum()]
        current_idx = get_current_line_index(proof)
        
        if current_idx != falsum_idx:
            rule = get_rule_by_name("R")
            justification = Justification(rule, (falsum_idx,))
            proof.add_line(Falsum(), justification)
        
        rule = get_rule_by_name("¬I")
        subproof_idx_tuple = find_nested_subproof_idx(proof, subproof_assumption_idx)
        if subproof_idx_tuple is None:
            cleanup_subproof_from_index(proof, subproof_assumption_idx)
            memo[goal_key] = False
            return False
        justification = Justification(rule, (subproof_idx_tuple,))
        proof.end_subproof(goal, justification)
        new_idx = get_current_line_index(proof)
        formula_to_idx[goal] = new_idx
        memo[goal_key] = True
        return True
    else:
        cleanup_subproof_from_index(proof, subproof_assumption_idx)
    
    return False


def backward_chain_indirect(proof, goal, formula_to_idx, depth, max_depth, memo, goal_key):
    assumption = Not(goal)
    proof.begin_subproof(assumption)
    subproof_assumption_idx = get_current_line_index(proof)
    
    subproof_formula_to_idx = formula_to_idx.copy()
    subproof_formula_to_idx[assumption] = subproof_assumption_idx
    
    if not forward_chain_in_subproof(proof, subproof_formula_to_idx, Falsum()):
        if backward_chain(
                proof, Falsum(), subproof_formula_to_idx, depth + 1, max_depth, memo):
            if not can_derive_immediately(Falsum(), subproof_formula_to_idx):
                cleanup_subproof_from_index(proof, subproof_assumption_idx)
                memo[goal_key] = False
                return False
        else:
            cleanup_subproof_from_index(proof, subproof_assumption_idx)
            memo[goal_key] = False
            return False
    
    if backward_chain(
            proof, Falsum(), subproof_formula_to_idx, depth + 1, max_depth, memo):
        if not can_derive_immediately(Falsum(), subproof_formula_to_idx):
            cleanup_subproof_from_index(proof, subproof_assumption_idx)
            memo[goal_key] = False
            return False
        
        falsum_idx = subproof_formula_to_idx[Falsum()]
        current_idx = get_current_line_index(proof)
        
        if current_idx != falsum_idx:
            rule = get_rule_by_name("R")
            justification = Justification(rule, (falsum_idx,))
            proof.add_line(Falsum(), justification)
        
        rule = get_rule_by_name("IP")
        subproof_idx_tuple = find_nested_subproof_idx(proof, subproof_assumption_idx)
        if subproof_idx_tuple is None:
            cleanup_subproof_from_index(proof, subproof_assumption_idx)
            memo[goal_key] = False
            return False
        justification = Justification(rule, (subproof_idx_tuple,))
        proof.end_subproof(goal, justification)
        new_idx = get_current_line_index(proof)
        formula_to_idx[goal] = new_idx
        memo[goal_key] = True
        return True
    else:
        cleanup_subproof_from_index(proof, subproof_assumption_idx)
    
    return False


# Backward chaining
def backward_chain(proof, goal, formula_to_idx, depth=0, max_depth=10, memo=None):
    if memo is None:
        memo = {}
    
    goal_key = (goal, depth)
    if goal_key in memo:
        return memo[goal_key]
    
    if depth >= max_depth:
        memo[goal_key] = False
        return False
    
    if can_derive_immediately(goal, formula_to_idx):
        memo[goal_key] = True
        return True
    
    match goal:
        case And():
            if backward_chain_and(
                    proof, goal, formula_to_idx, depth, max_depth, memo, goal_key):
                return True
    
    max_iterations = 20
    iteration = 0
    
    while iteration < max_iterations:
        new_formulas = forward_chain_iteration(proof, formula_to_idx, goal)
        formula_to_idx.update(new_formulas)
        
        if can_derive_immediately(goal, formula_to_idx):
            memo[goal_key] = True
            return True
        
        if not new_formulas:
            break
        
        iteration += 1
    
    match goal:
        case And():
            if backward_chain_and(
                    proof, goal, formula_to_idx, depth, max_depth, memo, goal_key):
                return True
        
        case Or():
            if backward_chain_or(
                    proof, goal, formula_to_idx, depth, max_depth, memo, goal_key):
                return True
        
        case Imp():
            if backward_chain_imp(
                    proof, goal, formula_to_idx, depth, max_depth, memo, goal_key):
                return True
        
        case Iff():
            if backward_chain_iff(
                    proof, goal, formula_to_idx, depth, max_depth, memo, goal_key):
                return True
        
        case PropVar() | Falsum():
            if backward_chain_atomic(
                    proof, goal, formula_to_idx, depth, max_depth, memo, goal_key):
                return True
        
        case Not():
            if backward_chain_not(
                    proof, goal, formula_to_idx, depth, max_depth, memo, goal_key):
                return True
    
    if Falsum() in formula_to_idx:
        falsum_idx = formula_to_idx[Falsum()]
        rule = get_rule_by_name("X")
        justification = Justification(rule, (falsum_idx,))
        proof.add_line(goal, justification)
        new_idx = get_current_line_index(proof)
        formula_to_idx[goal] = new_idx
        memo[goal_key] = True
        return True
    
    if backward_chain_indirect(
            proof, goal, formula_to_idx, depth, max_depth, memo, goal_key):
        return True
    
    memo[goal_key] = False
    return False
