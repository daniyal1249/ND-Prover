from .logic import *
from .tfl_semantic import is_valid


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


def can_derive_immediately(goal, available):
    return goal in available


def get_current_line_index(proof):
    return proof.proof.idx[1]


def find_subproof_by_start_idx(subproof, target_idx):
    if subproof.assumption:
        if subproof.seq and subproof.seq[0].is_line() and subproof.seq[0].idx == target_idx:
            return subproof
    for obj in subproof.seq:
        if obj.is_subproof():
            result = find_subproof_by_start_idx(obj, target_idx)
            if result is not None:
                return result
    return None


def get_rule_by_name(name):
    for rule in Rules.rules:
        if rule.name == name:
            return rule
    return None


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
    elif formula.right in formula_to_idx and formula.left in formula_to_idx and formula.left != formula.right:
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
            if result_formula not in formula_to_idx and result_formula not in new_formulas:
                new_formulas[result_formula] = result_idx
                if goal is not None and result_formula == goal:
                    return new_formulas
        
        results = apply_imp_elimination(proof, formula, formula_to_idx)
        for result_formula, result_idx in results:
            if result_formula not in formula_to_idx and result_formula not in new_formulas:
                new_formulas[result_formula] = result_idx
                if goal is not None and result_formula == goal:
                    return new_formulas
        
        results = apply_iff_elimination(proof, formula, formula_to_idx)
        for result_formula, result_idx in results:
            if result_formula not in formula_to_idx and result_formula not in new_formulas:
                new_formulas[result_formula] = result_idx
                if goal is not None and result_formula == goal:
                    return new_formulas
        
        results = apply_not_elimination(proof, formula, formula_to_idx)
        for result_formula, result_idx in results:
            if result_formula not in formula_to_idx and result_formula not in new_formulas:
                new_formulas[result_formula] = result_idx
                if goal is not None and result_formula == goal:
                    return new_formulas
        
        results = apply_dne(proof, formula, formula_to_idx)
        for result_formula, result_idx in results:
            if result_formula not in formula_to_idx and result_formula not in new_formulas:
                new_formulas[result_formula] = result_idx
                if goal is not None and result_formula == goal:
                    return new_formulas
        
        results = apply_demorgan(proof, formula, formula_to_idx)
        for result_formula, result_idx in results:
            if result_formula not in formula_to_idx and result_formula not in new_formulas:
                new_formulas[result_formula] = result_idx
                if goal is not None and result_formula == goal:
                    return new_formulas
        
        results = apply_mt(proof, formula, formula_to_idx)
        for result_formula, result_idx in results:
            if result_formula not in formula_to_idx and result_formula not in new_formulas:
                new_formulas[result_formula] = result_idx
                if goal is not None and result_formula == goal:
                    return new_formulas
        
        results = apply_ds(proof, formula, formula_to_idx)
        for result_formula, result_idx in results:
            if result_formula not in formula_to_idx and result_formula not in new_formulas:
                new_formulas[result_formula] = result_idx
                if goal is not None and result_formula == goal:
                    return new_formulas
    
    return new_formulas


def try_and_introduction(proof, goal, formula_to_idx, depth=0, max_depth=10):
    if not isinstance(goal, And):
        return None
    
    if depth >= max_depth:
        return None
    
    if goal.left not in formula_to_idx:
        return None
    
    if goal.right not in formula_to_idx:
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
    
    max_iterations = 20
    iteration = 0
    
    while iteration < max_iterations:
        new_formulas = forward_chain_iteration(proof, subproof_formula_to_idx)
        subproof_formula_to_idx.update(new_formulas)
        
        if can_derive_immediately(goal.right, subproof_formula_to_idx):
            break
        
        if not new_formulas:
            break
        
        iteration += 1
    
    if not can_derive_immediately(goal.right, subproof_formula_to_idx):
        while get_current_line_index(proof) >= subproof_assumption_idx:
            try:
                proof.delete_line()
            except:
                break
        return None
    
    right_idx = subproof_formula_to_idx[goal.right]
    final_idx = get_current_line_index(proof)
    
    if final_idx != right_idx:
        rule = get_rule_by_name("R")
        justification = Justification(rule, (right_idx,))
        proof.add_line(goal.right, justification)
    
    rule = get_rule_by_name("→I")
    subproof_idx_tuple = proof.proof.seq[-1].idx
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
    
    rule = get_rule_by_name("¬I")
    subproof_idx_tuple = proof.proof.seq[-1].idx
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
    subproof_idx_tuple = proof.proof.seq[-1].idx
    justification = Justification(rule, (subproof_idx_tuple,))
    proof.end_subproof(goal, justification)
    new_idx = get_current_line_index(proof)
    
    return new_idx


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
        case And(left, right):
            if left == right and can_derive_immediately(left, formula_to_idx):
                left_idx = formula_to_idx[left]
                rule = get_rule_by_name("∧I")
                justification = Justification(rule, (left_idx, left_idx))
                proof.add_line(goal, justification)
                new_idx = get_current_line_index(proof)
                formula_to_idx[goal] = new_idx
                memo[goal_key] = True
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
        case And(left, right):
            if can_derive_immediately(goal, formula_to_idx):
                memo[goal_key] = True
                return True
            
            if backward_chain(proof, left, formula_to_idx, depth + 1, max_depth, memo):
                if backward_chain(proof, right, formula_to_idx, depth + 1, max_depth, memo):
                    if can_derive_immediately(left, formula_to_idx) and can_derive_immediately(right, formula_to_idx):
                        idx = try_and_introduction(proof, goal, formula_to_idx, depth, max_depth)
                        if idx is not None:
                            formula_to_idx[goal] = idx
                            memo[goal_key] = True
                            return True
        
        case Or(left, right):
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
        
        case Imp(left, right):
            proof.begin_subproof(left)
            subproof_assumption_idx = get_current_line_index(proof)
            
            subproof_formula_to_idx = formula_to_idx.copy()
            subproof_formula_to_idx[left] = subproof_assumption_idx
            
            max_subproof_iterations = 20
            subproof_iteration = 0
            
            while subproof_iteration < max_subproof_iterations:
                new_formulas = forward_chain_iteration(proof, subproof_formula_to_idx, right)
                subproof_formula_to_idx.update(new_formulas)
                
                if can_derive_immediately(right, subproof_formula_to_idx):
                    break
                
                if not new_formulas:
                    break
                
                subproof_iteration += 1
            
            if backward_chain(proof, right, subproof_formula_to_idx, depth + 1, max_depth, memo):
                if not can_derive_immediately(right, subproof_formula_to_idx):
                    while get_current_line_index(proof) >= subproof_assumption_idx:
                        try:
                            proof.delete_line()
                        except:
                            break
                    memo[goal_key] = False
                    return False
                
                right_idx = subproof_formula_to_idx[right]
                
                active_subproof = find_subproof_by_start_idx(proof.proof, subproof_assumption_idx)
                if active_subproof is not None:
                    subproof_conclusion = active_subproof.conclusion
                    if subproof_conclusion == right:
                        pass
                    else:
                        rule = get_rule_by_name("R")
                        justification = Justification(rule, (right_idx,))
                        proof.add_line(right, justification)
                else:
                    current_idx = get_current_line_index(proof)
                    if current_idx != right_idx:
                        rule = get_rule_by_name("R")
                        justification = Justification(rule, (right_idx,))
                        proof.add_line(right, justification)
                
                rule = get_rule_by_name("→I")
                final_idx = get_current_line_index(proof)
                subproof_idx_tuple = (subproof_assumption_idx, final_idx)
                justification = Justification(rule, (subproof_idx_tuple,))
                proof.end_subproof(goal, justification)
                
                new_idx = get_current_line_index(proof)
                formula_to_idx[goal] = new_idx
                memo[goal_key] = True
                return True
            
            while get_current_line_index(proof) >= subproof_assumption_idx:
                try:
                    proof.delete_line()
                except:
                    break
        
        case Not(inner):
            proof.begin_subproof(inner)
            subproof_assumption_idx = get_current_line_index(proof)
            
            subproof_formula_to_idx = formula_to_idx.copy()
            subproof_formula_to_idx[inner] = subproof_assumption_idx
            
            max_subproof_iterations = 20
            subproof_iteration = 0
            
            while subproof_iteration < max_subproof_iterations:
                new_formulas = forward_chain_iteration(proof, subproof_formula_to_idx, Falsum())
                subproof_formula_to_idx.update(new_formulas)
                
                if can_derive_immediately(Falsum(), subproof_formula_to_idx):
                    break
                
                if not new_formulas:
                    break
                
                subproof_iteration += 1
            
            if backward_chain(proof, Falsum(), subproof_formula_to_idx, depth + 1, max_depth, memo):
                if not can_derive_immediately(Falsum(), subproof_formula_to_idx):
                    while get_current_line_index(proof) >= subproof_assumption_idx:
                        try:
                            proof.delete_line()
                        except:
                            break
                    memo[goal_key] = False
                    return False
                
                falsum_idx = subproof_formula_to_idx[Falsum()]
                current_idx = get_current_line_index(proof)
                
                if current_idx != falsum_idx:
                    rule = get_rule_by_name("R")
                    justification = Justification(rule, (falsum_idx,))
                    proof.add_line(Falsum(), justification)
                
                rule = get_rule_by_name("¬I")
                subproof_idx_tuple = proof.proof.seq[-1].idx
                justification = Justification(rule, (subproof_idx_tuple,))
                proof.end_subproof(goal, justification)
                new_idx = get_current_line_index(proof)
                formula_to_idx[goal] = new_idx
                memo[goal_key] = True
                return True
            else:
                while get_current_line_index(proof) >= subproof_assumption_idx:
                    try:
                        proof.delete_line()
                    except:
                        break
    
    if Falsum() in formula_to_idx:
        falsum_idx = formula_to_idx[Falsum()]
        rule = get_rule_by_name("X")
        justification = Justification(rule, (falsum_idx,))
        proof.add_line(goal, justification)
        new_idx = get_current_line_index(proof)
        formula_to_idx[goal] = new_idx
        memo[goal_key] = True
        return True
    
    assumption = Not(goal)
    proof.begin_subproof(assumption)
    subproof_assumption_idx = get_current_line_index(proof)
    
    subproof_formula_to_idx = formula_to_idx.copy()
    subproof_formula_to_idx[assumption] = subproof_assumption_idx
    
    max_subproof_iterations = 20
    subproof_iteration = 0
    
    while subproof_iteration < max_subproof_iterations:
        new_formulas = forward_chain_iteration(proof, subproof_formula_to_idx, Falsum())
        subproof_formula_to_idx.update(new_formulas)
        
        if can_derive_immediately(Falsum(), subproof_formula_to_idx):
            break
        
        if not new_formulas:
            break
        
        subproof_iteration += 1
    
    if backward_chain(proof, Falsum(), subproof_formula_to_idx, depth + 1, max_depth, memo):
        if not can_derive_immediately(Falsum(), subproof_formula_to_idx):
            while get_current_line_index(proof) >= subproof_assumption_idx:
                try:
                    proof.delete_line()
                except:
                    break
            memo[goal_key] = False
            return False
        
        falsum_idx = subproof_formula_to_idx[Falsum()]
        current_idx = get_current_line_index(proof)
        
        if current_idx != falsum_idx:
            rule = get_rule_by_name("R")
            justification = Justification(rule, (falsum_idx,))
            proof.add_line(Falsum(), justification)
        
        rule = get_rule_by_name("IP")
        subproof_idx_tuple = proof.proof.seq[-1].idx
        justification = Justification(rule, (subproof_idx_tuple,))
        proof.end_subproof(goal, justification)
        new_idx = get_current_line_index(proof)
        formula_to_idx[goal] = new_idx
        memo[goal_key] = True
        return True
    else:
        while get_current_line_index(proof) >= subproof_assumption_idx:
            try:
                proof.delete_line()
            except:
                break
    
    memo[goal_key] = False
    return False



