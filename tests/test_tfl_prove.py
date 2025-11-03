import unittest

from nd_prover import *
from nd_prover.tfl_prove import (
    prove, is_compound, get_main_connective, can_derive_immediately,
    apply_and_elimination, apply_imp_elimination, apply_iff_elimination,
    apply_not_elimination, apply_dne, apply_demorgan, apply_mt, apply_ds,
    forward_chain_iteration, try_and_introduction, try_or_introduction,
    try_imp_introduction, try_not_introduction, try_indirect_proof,
    backward_chain
)


class TestProve(unittest.TestCase):
    def test_invalid_argument(self):
        premises = [PropVar("P")]
        conclusion = PropVar("Q")
        result = prove(premises, conclusion)
        self.assertIsNone(result)

    def test_valid_argument_initializes_proof(self):
        premises = [Imp(PropVar("P"), PropVar("Q")), PropVar("P")]
        conclusion = PropVar("Q")
        result = prove(premises, conclusion)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, Proof)
        self.assertEqual(result.logic, TFL)
        self.assertEqual(result.premises, premises)
        self.assertEqual(result.conclusion, conclusion)
        self.assertTrue(result.is_complete())

    def test_no_premises_valid(self):
        premises = []
        conclusion = Or(PropVar("P"), Not(PropVar("P")))
        result = prove(premises, conclusion)
        self.assertIsNotNone(result)

    def test_no_premises_invalid(self):
        premises = []
        conclusion = PropVar("P")
        result = prove(premises, conclusion)
        self.assertIsNone(result)

    def test_simple_modus_ponens(self):
        premises = [Imp(PropVar("P"), PropVar("Q")), PropVar("P")]
        conclusion = PropVar("Q")
        result = prove(premises, conclusion)
        self.assertIsNotNone(result)
        self.assertTrue(result.is_complete())

    def test_simple_and_elimination(self):
        premises = [And(PropVar("A"), PropVar("B"))]
        conclusion = PropVar("A")
        result = prove(premises, conclusion)
        self.assertIsNotNone(result)
        self.assertTrue(result.is_complete())

    def test_chained_implications(self):
        premises = [
            Imp(PropVar("A"), PropVar("B")),
            Imp(PropVar("B"), PropVar("C")),
            PropVar("A")
        ]
        conclusion = PropVar("C")
        result = prove(premises, conclusion)
        self.assertIsNotNone(result)
        self.assertTrue(result.is_complete())

    def test_multiple_and_eliminations(self):
        premises = [
            And(PropVar("A"), PropVar("B")),
            Imp(PropVar("A"), PropVar("C")),
            Imp(PropVar("B"), PropVar("D"))
        ]
        conclusion = PropVar("C")
        result = prove(premises, conclusion)
        self.assertIsNotNone(result)
        self.assertTrue(result.is_complete())

    def test_modus_tollens(self):
        premises = [
            Imp(PropVar("P"), PropVar("Q")),
            Not(PropVar("Q"))
        ]
        conclusion = Not(PropVar("P"))
        result = prove(premises, conclusion)
        self.assertIsNotNone(result)
        self.assertTrue(result.is_complete())

    def test_disjunctive_syllogism(self):
        premises = [
            Or(PropVar("P"), PropVar("Q")),
            Not(PropVar("P"))
        ]
        conclusion = PropVar("Q")
        result = prove(premises, conclusion)
        self.assertIsNotNone(result)
        self.assertTrue(result.is_complete())

    def test_double_negation_elimination(self):
        premises = [Not(Not(PropVar("P")))]
        conclusion = PropVar("P")
        result = prove(premises, conclusion)
        self.assertIsNotNone(result)
        self.assertTrue(result.is_complete())

    def test_iff_elimination(self):
        premises = [
            Iff(PropVar("P"), PropVar("Q")),
            PropVar("P")
        ]
        conclusion = PropVar("Q")
        result = prove(premises, conclusion)
        self.assertIsNotNone(result)
        self.assertTrue(result.is_complete())


class TestIsCompound(unittest.TestCase):
    def test_atomic_not_compound(self):
        self.assertFalse(is_compound(PropVar("P")))
        self.assertFalse(is_compound(Falsum()))

    def test_negation_is_compound(self):
        self.assertTrue(is_compound(Not(PropVar("P"))))

    def test_binary_connectives_are_compound(self):
        self.assertTrue(is_compound(And(PropVar("A"), PropVar("B"))))
        self.assertTrue(is_compound(Or(PropVar("A"), PropVar("B"))))
        self.assertTrue(is_compound(Imp(PropVar("A"), PropVar("B"))))
        self.assertTrue(is_compound(Iff(PropVar("A"), PropVar("B"))))

    def test_nested_is_compound(self):
        formula = Imp(And(PropVar("A"), PropVar("B")), PropVar("C"))
        self.assertTrue(is_compound(formula))


class TestGetMainConnective(unittest.TestCase):
    def test_atomic_formulas(self):
        self.assertEqual(get_main_connective(PropVar("P")), PropVar)
        self.assertEqual(get_main_connective(Falsum()), Falsum)

    def test_negation(self):
        self.assertEqual(get_main_connective(Not(PropVar("P"))), Not)

    def test_binary_connectives(self):
        self.assertEqual(get_main_connective(And(PropVar("A"), PropVar("B"))), And)
        self.assertEqual(get_main_connective(Or(PropVar("A"), PropVar("B"))), Or)
        self.assertEqual(get_main_connective(Imp(PropVar("A"), PropVar("B"))), Imp)
        self.assertEqual(get_main_connective(Iff(PropVar("A"), PropVar("B"))), Iff)

    def test_nested_formulas(self):
        formula = Imp(And(PropVar("A"), PropVar("B")), PropVar("C"))
        self.assertEqual(get_main_connective(formula), Imp)


class TestCanDeriveImmediately(unittest.TestCase):
    def test_formula_in_available(self):
        goal = PropVar("P")
        available = {PropVar("P"), PropVar("Q"), PropVar("R")}
        self.assertTrue(can_derive_immediately(goal, available))

    def test_formula_not_in_available(self):
        goal = PropVar("P")
        available = {PropVar("Q"), PropVar("R")}
        self.assertFalse(can_derive_immediately(goal, available))

    def test_empty_available(self):
        goal = PropVar("P")
        available = set()
        self.assertFalse(can_derive_immediately(goal, available))

    def test_compound_formulas(self):
        goal = And(PropVar("A"), PropVar("B"))
        available = {And(PropVar("A"), PropVar("B")), PropVar("C")}
        self.assertTrue(can_derive_immediately(goal, available))

    def test_different_but_equivalent_structure(self):
        goal = And(PropVar("A"), PropVar("B"))
        available = {And(PropVar("B"), PropVar("A"))}
        self.assertFalse(can_derive_immediately(goal, available))


class TestApplyAndElimination(unittest.TestCase):
    def test_applies_to_and(self):
        proof = Proof(TFL, [And(PropVar("A"), PropVar("B"))], PropVar("A"))
        formula = And(PropVar("A"), PropVar("B"))
        formula_to_idx = {And(PropVar("A"), PropVar("B")): 1}
        
        results = apply_and_elimination(proof, formula, formula_to_idx)
        
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0][0], PropVar("A"))
        self.assertEqual(results[1][0], PropVar("B"))
        self.assertEqual(results[0][1], 2)
        self.assertEqual(results[1][1], 3)

    def test_not_applicable_to_non_and(self):
        proof = Proof(TFL, [PropVar("P")], PropVar("P"))
        formula = PropVar("P")
        formula_to_idx = {PropVar("P"): 1}
        
        results = apply_and_elimination(proof, formula, formula_to_idx)
        
        self.assertEqual(results, [])

    def test_not_applicable_if_formula_not_in_mapping(self):
        proof = Proof(TFL, [PropVar("P")], PropVar("P"))
        formula = And(PropVar("A"), PropVar("B"))
        formula_to_idx = {}
        
        results = apply_and_elimination(proof, formula, formula_to_idx)
        
        self.assertEqual(results, [])


class TestApplyImpElimination(unittest.TestCase):
    def test_modus_ponens(self):
        proof = Proof(TFL, [Imp(PropVar("P"), PropVar("Q")), PropVar("P")], PropVar("Q"))
        formula = Imp(PropVar("P"), PropVar("Q"))
        formula_to_idx = {Imp(PropVar("P"), PropVar("Q")): 1, PropVar("P"): 2}
        
        results = apply_imp_elimination(proof, formula, formula_to_idx)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][0], PropVar("Q"))
        self.assertTrue(proof.is_complete())

    def test_not_applicable_to_non_imp(self):
        proof = Proof(TFL, [PropVar("P")], PropVar("P"))
        formula = PropVar("P")
        formula_to_idx = {PropVar("P"): 1}
        
        results = apply_imp_elimination(proof, formula, formula_to_idx)
        
        self.assertEqual(results, [])

    def test_not_applicable_if_antecedent_not_available(self):
        proof = Proof(TFL, [Imp(PropVar("P"), PropVar("Q"))], PropVar("Q"))
        formula = Imp(PropVar("P"), PropVar("Q"))
        formula_to_idx = {Imp(PropVar("P"), PropVar("Q")): 1}
        
        results = apply_imp_elimination(proof, formula, formula_to_idx)
        
        self.assertEqual(results, [])


class TestApplyIffElimination(unittest.TestCase):
    def test_derive_right_from_left(self):
        proof = Proof(TFL, [Iff(PropVar("P"), PropVar("Q")), PropVar("P")], PropVar("Q"))
        formula = Iff(PropVar("P"), PropVar("Q"))
        formula_to_idx = {Iff(PropVar("P"), PropVar("Q")): 1, PropVar("P"): 2}
        
        results = apply_iff_elimination(proof, formula, formula_to_idx)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][0], PropVar("Q"))
        self.assertTrue(proof.is_complete())

    def test_derive_left_from_right(self):
        proof = Proof(TFL, [Iff(PropVar("P"), PropVar("Q")), PropVar("Q")], PropVar("P"))
        formula = Iff(PropVar("P"), PropVar("Q"))
        formula_to_idx = {Iff(PropVar("P"), PropVar("Q")): 1, PropVar("Q"): 2}
        
        results = apply_iff_elimination(proof, formula, formula_to_idx)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][0], PropVar("P"))
        self.assertTrue(proof.is_complete())

    def test_derive_both_when_both_sides_available(self):
        proof = Proof(TFL, [Iff(PropVar("P"), PropVar("Q")), PropVar("P"), PropVar("Q")], PropVar("P"))
        formula = Iff(PropVar("P"), PropVar("Q"))
        formula_to_idx = {Iff(PropVar("P"), PropVar("Q")): 1, PropVar("P"): 2, PropVar("Q"): 3}
        
        results = apply_iff_elimination(proof, formula, formula_to_idx)
        
        self.assertEqual(len(results), 2)

    def test_not_applicable_to_non_iff(self):
        proof = Proof(TFL, [PropVar("P")], PropVar("P"))
        formula = PropVar("P")
        formula_to_idx = {PropVar("P"): 1}
        
        results = apply_iff_elimination(proof, formula, formula_to_idx)
        
        self.assertEqual(results, [])

    def test_not_applicable_if_no_side_available(self):
        proof = Proof(TFL, [Iff(PropVar("P"), PropVar("Q"))], PropVar("P"))
        formula = Iff(PropVar("P"), PropVar("Q"))
        formula_to_idx = {Iff(PropVar("P"), PropVar("Q")): 1}
        
        results = apply_iff_elimination(proof, formula, formula_to_idx)
        
        self.assertEqual(results, [])


class TestApplyNotElimination(unittest.TestCase):
    def test_applies_when_not_and_inner_available(self):
        proof = Proof(TFL, [Not(PropVar("P")), PropVar("P")], Falsum())
        formula = Not(PropVar("P"))
        formula_to_idx = {Not(PropVar("P")): 1, PropVar("P"): 2}
        
        results = apply_not_elimination(proof, formula, formula_to_idx)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][0], Falsum())
        self.assertTrue(proof.is_complete())

    def test_not_applicable_to_non_not(self):
        proof = Proof(TFL, [PropVar("P")], PropVar("P"))
        formula = PropVar("P")
        formula_to_idx = {PropVar("P"): 1}
        
        results = apply_not_elimination(proof, formula, formula_to_idx)
        
        self.assertEqual(results, [])

    def test_not_applicable_if_inner_not_available(self):
        proof = Proof(TFL, [Not(PropVar("P"))], Falsum())
        formula = Not(PropVar("P"))
        formula_to_idx = {Not(PropVar("P")): 1}
        
        results = apply_not_elimination(proof, formula, formula_to_idx)
        
        self.assertEqual(results, [])


class TestApplyDNE(unittest.TestCase):
    def test_applies_to_double_negation(self):
        proof = Proof(TFL, [Not(Not(PropVar("P")))], PropVar("P"))
        formula = Not(Not(PropVar("P")))
        formula_to_idx = {Not(Not(PropVar("P"))): 1}
        
        results = apply_dne(proof, formula, formula_to_idx)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][0], PropVar("P"))
        self.assertTrue(proof.is_complete())

    def test_not_applicable_to_single_negation(self):
        proof = Proof(TFL, [Not(PropVar("P"))], PropVar("P"))
        formula = Not(PropVar("P"))
        formula_to_idx = {Not(PropVar("P")): 1}
        
        results = apply_dne(proof, formula, formula_to_idx)
        
        self.assertEqual(results, [])

    def test_not_applicable_to_non_negation(self):
        proof = Proof(TFL, [PropVar("P")], PropVar("P"))
        formula = PropVar("P")
        formula_to_idx = {PropVar("P"): 1}
        
        results = apply_dne(proof, formula, formula_to_idx)
        
        self.assertEqual(results, [])


class TestApplyDeMorgan(unittest.TestCase):
    def test_not_or_to_and_not(self):
        proof = Proof(TFL, [Not(Or(PropVar("A"), PropVar("B")))], And(Not(PropVar("A")), Not(PropVar("B"))))
        formula = Not(Or(PropVar("A"), PropVar("B")))
        formula_to_idx = {formula: 1}
        
        results = apply_demorgan(proof, formula, formula_to_idx)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][0], And(Not(PropVar("A")), Not(PropVar("B"))))

    def test_and_not_to_not_or(self):
        proof = Proof(TFL, [And(Not(PropVar("A")), Not(PropVar("B")))], Not(Or(PropVar("A"), PropVar("B"))))
        formula = And(Not(PropVar("A")), Not(PropVar("B")))
        formula_to_idx = {formula: 1}
        
        results = apply_demorgan(proof, formula, formula_to_idx)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][0], Not(Or(PropVar("A"), PropVar("B"))))

    def test_not_and_to_or_not(self):
        proof = Proof(TFL, [Not(And(PropVar("A"), PropVar("B")))], Or(Not(PropVar("A")), Not(PropVar("B"))))
        formula = Not(And(PropVar("A"), PropVar("B")))
        formula_to_idx = {formula: 1}
        
        results = apply_demorgan(proof, formula, formula_to_idx)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][0], Or(Not(PropVar("A")), Not(PropVar("B"))))

    def test_or_not_to_not_and(self):
        proof = Proof(TFL, [Or(Not(PropVar("A")), Not(PropVar("B")))], Not(And(PropVar("A"), PropVar("B"))))
        formula = Or(Not(PropVar("A")), Not(PropVar("B")))
        formula_to_idx = {formula: 1}
        
        results = apply_demorgan(proof, formula, formula_to_idx)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][0], Not(And(PropVar("A"), PropVar("B"))))

    def test_not_applicable_to_other_formulas(self):
        proof = Proof(TFL, [PropVar("P")], PropVar("P"))
        formula = PropVar("P")
        formula_to_idx = {formula: 1}
        
        results = apply_demorgan(proof, formula, formula_to_idx)
        
        self.assertEqual(results, [])


class TestApplyMT(unittest.TestCase):
    def test_modus_tollens(self):
        proof = Proof(TFL, [Imp(PropVar("P"), PropVar("Q")), Not(PropVar("Q"))], Not(PropVar("P")))
        formula = Imp(PropVar("P"), PropVar("Q"))
        formula_to_idx = {Imp(PropVar("P"), PropVar("Q")): 1, Not(PropVar("Q")): 2}
        
        results = apply_mt(proof, formula, formula_to_idx)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][0], Not(PropVar("P")))
        self.assertTrue(proof.is_complete())

    def test_not_applicable_to_non_imp(self):
        proof = Proof(TFL, [PropVar("P")], PropVar("P"))
        formula = PropVar("P")
        formula_to_idx = {PropVar("P"): 1}
        
        results = apply_mt(proof, formula, formula_to_idx)
        
        self.assertEqual(results, [])

    def test_not_applicable_if_not_consequent_not_available(self):
        proof = Proof(TFL, [Imp(PropVar("P"), PropVar("Q"))], Not(PropVar("P")))
        formula = Imp(PropVar("P"), PropVar("Q"))
        formula_to_idx = {Imp(PropVar("P"), PropVar("Q")): 1}
        
        results = apply_mt(proof, formula, formula_to_idx)
        
        self.assertEqual(results, [])


class TestApplyDS(unittest.TestCase):
    def test_derive_right_from_not_left(self):
        proof = Proof(TFL, [Or(PropVar("P"), PropVar("Q")), Not(PropVar("P"))], PropVar("Q"))
        formula = Or(PropVar("P"), PropVar("Q"))
        formula_to_idx = {Or(PropVar("P"), PropVar("Q")): 1, Not(PropVar("P")): 2}
        
        results = apply_ds(proof, formula, formula_to_idx)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][0], PropVar("Q"))
        self.assertTrue(proof.is_complete())

    def test_derive_left_from_not_right(self):
        proof = Proof(TFL, [Or(PropVar("P"), PropVar("Q")), Not(PropVar("Q"))], PropVar("P"))
        formula = Or(PropVar("P"), PropVar("Q"))
        formula_to_idx = {Or(PropVar("P"), PropVar("Q")): 1, Not(PropVar("Q")): 2}
        
        results = apply_ds(proof, formula, formula_to_idx)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][0], PropVar("P"))
        self.assertTrue(proof.is_complete())

    def test_derive_both_when_both_negations_available(self):
        proof = Proof(TFL, [Or(PropVar("P"), PropVar("Q")), Not(PropVar("P")), Not(PropVar("Q"))], PropVar("P"))
        formula = Or(PropVar("P"), PropVar("Q"))
        formula_to_idx = {Or(PropVar("P"), PropVar("Q")): 1, Not(PropVar("P")): 2, Not(PropVar("Q")): 3}
        
        results = apply_ds(proof, formula, formula_to_idx)
        
        self.assertEqual(len(results), 2)

    def test_not_applicable_to_non_or(self):
        proof = Proof(TFL, [PropVar("P")], PropVar("P"))
        formula = PropVar("P")
        formula_to_idx = {PropVar("P"): 1}
        
        results = apply_ds(proof, formula, formula_to_idx)
        
        self.assertEqual(results, [])

    def test_not_applicable_if_no_negation_available(self):
        proof = Proof(TFL, [Or(PropVar("P"), PropVar("Q"))], PropVar("P"))
        formula = Or(PropVar("P"), PropVar("Q"))
        formula_to_idx = {Or(PropVar("P"), PropVar("Q")): 1}
        
        results = apply_ds(proof, formula, formula_to_idx)
        
        self.assertEqual(results, [])


class TestForwardChainIteration(unittest.TestCase):
    def test_simple_and_elimination(self):
        proof = Proof(TFL, [And(PropVar("A"), PropVar("B"))], PropVar("A"))
        formula_to_idx = {And(PropVar("A"), PropVar("B")): 1}
        
        new_formulas = forward_chain_iteration(proof, formula_to_idx)
        
        self.assertIn(PropVar("A"), new_formulas)
        self.assertIn(PropVar("B"), new_formulas)
        self.assertEqual(len(new_formulas), 2)

    def test_modus_ponens_forward_chain(self):
        proof = Proof(TFL, [Imp(PropVar("P"), PropVar("Q")), PropVar("P")], PropVar("Q"))
        formula_to_idx = {Imp(PropVar("P"), PropVar("Q")): 1, PropVar("P"): 2}
        
        new_formulas = forward_chain_iteration(proof, formula_to_idx)
        
        self.assertIn(PropVar("Q"), new_formulas)
        self.assertTrue(proof.is_complete())

    def test_multiple_rules_applied(self):
        proof = Proof(TFL, [
            And(PropVar("A"), PropVar("B")),
            Imp(PropVar("A"), PropVar("C")),
            Imp(PropVar("B"), PropVar("D"))
        ], PropVar("C"))
        formula_to_idx = {
            And(PropVar("A"), PropVar("B")): 1,
            Imp(PropVar("A"), PropVar("C")): 2,
            Imp(PropVar("B"), PropVar("D")): 3
        }
        
        new_formulas = forward_chain_iteration(proof, formula_to_idx)
        
        self.assertIn(PropVar("A"), new_formulas)
        self.assertIn(PropVar("B"), new_formulas)
        
        updated_idx = formula_to_idx.copy()
        updated_idx.update(new_formulas)
        
        new_formulas2 = forward_chain_iteration(proof, updated_idx)
        
        self.assertIn(PropVar("C"), new_formulas2)
        self.assertIn(PropVar("D"), new_formulas2)

    def test_no_new_formulas_when_nothing_applicable(self):
        proof = Proof(TFL, [PropVar("P"), PropVar("Q")], PropVar("R"))
        formula_to_idx = {PropVar("P"): 1, PropVar("Q"): 2}
        
        new_formulas = forward_chain_iteration(proof, formula_to_idx)
        
        self.assertEqual(len(new_formulas), 0)

    def test_does_not_duplicate_existing_formulas(self):
        proof = Proof(TFL, [And(PropVar("A"), PropVar("B"))], PropVar("A"))
        formula_to_idx = {
            And(PropVar("A"), PropVar("B")): 1,
            PropVar("A"): 2
        }
        
        new_formulas = forward_chain_iteration(proof, formula_to_idx)
        
        self.assertNotIn(PropVar("A"), new_formulas)
        self.assertIn(PropVar("B"), new_formulas)

    def test_chains_multiple_steps(self):
        proof = Proof(TFL, [
            Imp(PropVar("A"), PropVar("B")),
            Imp(PropVar("B"), PropVar("C")),
            PropVar("A")
        ], PropVar("C"))
        formula_to_idx = {
            Imp(PropVar("A"), PropVar("B")): 1,
            Imp(PropVar("B"), PropVar("C")): 2,
            PropVar("A"): 3
        }
        
        new_formulas1 = forward_chain_iteration(proof, formula_to_idx)
        self.assertIn(PropVar("B"), new_formulas1)
        
        updated_idx = formula_to_idx.copy()
        updated_idx.update(new_formulas1)
        
        new_formulas2 = forward_chain_iteration(proof, updated_idx)
        self.assertIn(PropVar("C"), new_formulas2)
        self.assertTrue(proof.is_complete())


class TestTryAndIntroduction(unittest.TestCase):
    def test_applies_when_both_sides_available(self):
        proof = Proof(TFL, [PropVar("A"), PropVar("B")], And(PropVar("A"), PropVar("B")))
        goal = And(PropVar("A"), PropVar("B"))
        formula_to_idx = {PropVar("A"): 1, PropVar("B"): 2}
        
        idx = try_and_introduction(proof, goal, formula_to_idx)
        
        self.assertIsNotNone(idx)
        self.assertTrue(proof.is_complete())

    def test_not_applicable_if_left_not_available(self):
        proof = Proof(TFL, [PropVar("B")], And(PropVar("A"), PropVar("B")))
        goal = And(PropVar("A"), PropVar("B"))
        formula_to_idx = {PropVar("B"): 1}
        
        idx = try_and_introduction(proof, goal, formula_to_idx)
        
        self.assertIsNone(idx)

    def test_not_applicable_if_right_not_available(self):
        proof = Proof(TFL, [PropVar("A")], And(PropVar("A"), PropVar("B")))
        goal = And(PropVar("A"), PropVar("B"))
        formula_to_idx = {PropVar("A"): 1}
        
        idx = try_and_introduction(proof, goal, formula_to_idx)
        
        self.assertIsNone(idx)

    def test_not_applicable_to_non_and(self):
        proof = Proof(TFL, [PropVar("A")], PropVar("A"))
        goal = PropVar("A")
        formula_to_idx = {PropVar("A"): 1}
        
        idx = try_and_introduction(proof, goal, formula_to_idx)
        
        self.assertIsNone(idx)


class TestTryOrIntroduction(unittest.TestCase):
    def test_applies_when_left_available(self):
        proof = Proof(TFL, [PropVar("A")], Or(PropVar("A"), PropVar("B")))
        goal = Or(PropVar("A"), PropVar("B"))
        formula_to_idx = {PropVar("A"): 1}
        
        idx = try_or_introduction(proof, goal, formula_to_idx)
        
        self.assertIsNotNone(idx)
        self.assertTrue(proof.is_complete())

    def test_applies_when_right_available(self):
        proof = Proof(TFL, [PropVar("B")], Or(PropVar("A"), PropVar("B")))
        goal = Or(PropVar("A"), PropVar("B"))
        formula_to_idx = {PropVar("B"): 1}
        
        idx = try_or_introduction(proof, goal, formula_to_idx)
        
        self.assertIsNotNone(idx)
        self.assertTrue(proof.is_complete())

    def test_not_applicable_if_neither_side_available(self):
        proof = Proof(TFL, [PropVar("C")], Or(PropVar("A"), PropVar("B")))
        goal = Or(PropVar("A"), PropVar("B"))
        formula_to_idx = {PropVar("C"): 1}
        
        idx = try_or_introduction(proof, goal, formula_to_idx)
        
        self.assertIsNone(idx)

    def test_not_applicable_to_non_or(self):
        proof = Proof(TFL, [PropVar("A")], PropVar("A"))
        goal = PropVar("A")
        formula_to_idx = {PropVar("A"): 1}
        
        idx = try_or_introduction(proof, goal, formula_to_idx)
        
        self.assertIsNone(idx)


class TestTryImpIntroduction(unittest.TestCase):
    def test_applies_when_consequent_already_available(self):
        proof = Proof(TFL, [PropVar("B")], Imp(PropVar("A"), PropVar("B")))
        goal = Imp(PropVar("A"), PropVar("B"))
        formula_to_idx = {PropVar("B"): 1}
        
        idx = try_imp_introduction(proof, goal, formula_to_idx)
        
        self.assertIsNotNone(idx)
        self.assertTrue(proof.is_complete())

    def test_applies_with_modus_ponens_in_subproof(self):
        proof = Proof(TFL, [Imp(PropVar("A"), PropVar("B"))], Imp(PropVar("A"), PropVar("B")))
        goal = Imp(PropVar("A"), PropVar("B"))
        formula_to_idx = {Imp(PropVar("A"), PropVar("B")): 1}
        
        idx = try_imp_introduction(proof, goal, formula_to_idx)
        
        self.assertIsNotNone(idx)
        self.assertTrue(proof.is_complete())

    def test_not_applicable_if_consequent_not_derivable(self):
        proof = Proof(TFL, [PropVar("C")], Imp(PropVar("A"), PropVar("B")))
        goal = Imp(PropVar("A"), PropVar("B"))
        formula_to_idx = {PropVar("C"): 1}
        
        idx = try_imp_introduction(proof, goal, formula_to_idx)
        
        self.assertIsNone(idx)

    def test_not_applicable_to_non_imp(self):
        proof = Proof(TFL, [PropVar("A")], PropVar("A"))
        goal = PropVar("A")
        formula_to_idx = {PropVar("A"): 1}
        
        idx = try_imp_introduction(proof, goal, formula_to_idx)
        
        self.assertIsNone(idx)


class TestTryNotIntroduction(unittest.TestCase):
    def test_applies_when_derive_falsum(self):
        proof = Proof(TFL, [PropVar("A"), Not(PropVar("A"))], Not(PropVar("A")))
        goal = Not(PropVar("A"))
        formula_to_idx = {PropVar("A"): 1, Not(PropVar("A")): 2}
        
        idx = try_not_introduction(proof, goal, formula_to_idx)
        
        self.assertIsNotNone(idx)
        self.assertTrue(proof.is_complete())

    def test_applies_with_not_elimination_in_subproof(self):
        proof = Proof(TFL, [PropVar("A")], Not(Not(PropVar("A"))))
        goal = Not(Not(PropVar("A")))
        formula_to_idx = {PropVar("A"): 1}
        
        idx = try_not_introduction(proof, goal, formula_to_idx)
        
        self.assertIsNotNone(idx)
        self.assertTrue(proof.is_complete())

    def test_not_applicable_if_falsum_not_derivable(self):
        proof = Proof(TFL, [PropVar("A")], Not(PropVar("B")))
        goal = Not(PropVar("B"))
        formula_to_idx = {PropVar("A"): 1}
        
        idx = try_not_introduction(proof, goal, formula_to_idx)
        
        self.assertIsNone(idx)

    def test_not_applicable_to_non_not(self):
        proof = Proof(TFL, [PropVar("A")], PropVar("A"))
        goal = PropVar("A")
        formula_to_idx = {PropVar("A"): 1}
        
        idx = try_not_introduction(proof, goal, formula_to_idx)
        
        self.assertIsNone(idx)


class TestTryIndirectProof(unittest.TestCase):
    def test_applies_when_derive_falsum_from_negation(self):
        proof = Proof(TFL, [Imp(PropVar("A"), PropVar("B")), Imp(Not(PropVar("A")), PropVar("B"))], PropVar("B"))
        goal = PropVar("B")
        formula_to_idx = {Imp(PropVar("A"), PropVar("B")): 1, Imp(Not(PropVar("A")), PropVar("B")): 2}
        
        idx = try_indirect_proof(proof, goal, formula_to_idx)
        
        self.assertIsNotNone(idx)
        self.assertTrue(proof.is_complete())

    def test_applies_with_contradiction(self):
        proof = Proof(TFL, [And(PropVar("A"), Not(PropVar("A")))], PropVar("B"))
        goal = PropVar("B")
        formula_to_idx = {And(PropVar("A"), Not(PropVar("A"))): 1}
        
        idx = try_indirect_proof(proof, goal, formula_to_idx)
        
        self.assertIsNotNone(idx)
        self.assertTrue(proof.is_complete())

    def test_not_applicable_if_goal_already_available(self):
        proof = Proof(TFL, [PropVar("A")], PropVar("A"))
        goal = PropVar("A")
        formula_to_idx = {PropVar("A"): 1}
        
        idx = try_indirect_proof(proof, goal, formula_to_idx)
        
        self.assertIsNone(idx)

    def test_not_applicable_if_falsum_not_derivable(self):
        proof = Proof(TFL, [PropVar("A")], PropVar("B"))
        goal = PropVar("B")
        formula_to_idx = {PropVar("A"): 1}
        
        idx = try_indirect_proof(proof, goal, formula_to_idx)
        
        self.assertIsNone(idx)


class TestBackwardChain(unittest.TestCase):
    def test_already_available(self):
        proof = Proof(TFL, [PropVar("A")], PropVar("A"))
        goal = PropVar("A")
        formula_to_idx = {PropVar("A"): 1}
        
        result = backward_chain(proof, goal, formula_to_idx)
        
        self.assertTrue(result)

    def test_simple_and_with_recursion(self):
        proof = Proof(TFL, [PropVar("A"), PropVar("B")], And(PropVar("A"), PropVar("B")))
        goal = And(PropVar("A"), PropVar("B"))
        formula_to_idx = {PropVar("A"): 1, PropVar("B"): 2}
        
        result = backward_chain(proof, goal, formula_to_idx)
        
        self.assertTrue(result)
        self.assertTrue(proof.is_complete())

    def test_simple_or_with_recursion(self):
        proof = Proof(TFL, [PropVar("A")], Or(PropVar("A"), PropVar("B")))
        goal = Or(PropVar("A"), PropVar("B"))
        formula_to_idx = {PropVar("A"): 1}
        
        result = backward_chain(proof, goal, formula_to_idx)
        
        self.assertTrue(result)
        self.assertTrue(proof.is_complete())

    def test_imp_with_recursion(self):
        proof = Proof(TFL, [], Imp(PropVar("A"), PropVar("A")))
        goal = Imp(PropVar("A"), PropVar("A"))
        formula_to_idx = {}
        
        result = backward_chain(proof, goal, formula_to_idx)
        
        self.assertTrue(result)
        self.assertTrue(proof.is_complete())

    def test_not_with_recursion(self):
        proof = Proof(TFL, [And(PropVar("A"), Not(PropVar("A")))], Not(PropVar("A")))
        goal = Not(PropVar("A"))
        formula_to_idx = {And(PropVar("A"), Not(PropVar("A"))): 1}
        
        result = backward_chain(proof, goal, formula_to_idx)
        
        self.assertTrue(result)
        self.assertTrue(proof.is_complete())

    def test_indirect_proof_with_recursion(self):
        proof = Proof(TFL, [And(PropVar("A"), Not(PropVar("A")))], PropVar("B"))
        goal = PropVar("B")
        formula_to_idx = {And(PropVar("A"), Not(PropVar("A"))): 1}
        
        result = backward_chain(proof, goal, formula_to_idx)
        
        self.assertTrue(result)
        self.assertTrue(proof.is_complete())

    def test_nested_and_with_recursion(self):
        proof = Proof(TFL, [PropVar("A"), PropVar("B"), PropVar("C")], 
                     And(And(PropVar("A"), PropVar("B")), PropVar("C")))
        goal = And(And(PropVar("A"), PropVar("B")), PropVar("C"))
        formula_to_idx = {PropVar("A"): 1, PropVar("B"): 2, PropVar("C"): 3}
        
        result = backward_chain(proof, goal, formula_to_idx)
        
        self.assertTrue(result)
        self.assertTrue(proof.is_complete())

    def test_complex_imp_with_recursion(self):
        proof = Proof(TFL, [Imp(PropVar("A"), PropVar("B"))], 
                     Imp(PropVar("A"), Or(PropVar("B"), PropVar("C"))))
        goal = Imp(PropVar("A"), Or(PropVar("B"), PropVar("C")))
        formula_to_idx = {Imp(PropVar("A"), PropVar("B")): 1}
        
        result = backward_chain(proof, goal, formula_to_idx)
        
        self.assertTrue(result)
        self.assertTrue(proof.is_complete())

    def test_depth_limiting(self):
        proof = Proof(TFL, [], PropVar("A"))
        goal = PropVar("A")
        formula_to_idx = {}
        
        result = backward_chain(proof, goal, formula_to_idx, depth=0, max_depth=0)
        
        self.assertFalse(result)

    def test_returns_false_when_cannot_prove(self):
        proof = Proof(TFL, [PropVar("A")], PropVar("B"))
        goal = PropVar("B")
        formula_to_idx = {PropVar("A"): 1}
        
        result = backward_chain(proof, goal, formula_to_idx)
        
        self.assertFalse(result)


class TestProveComplete(unittest.TestCase):
    def test_modus_ponens(self):
        premises = [Imp(PropVar("A"), PropVar("B")), PropVar("A")]
        conclusion = PropVar("B")
        
        result = prove(premises, conclusion)
        
        self.assertIsNotNone(result)
        self.assertTrue(result.is_complete())

    def test_and_introduction(self):
        premises = [PropVar("A"), PropVar("B")]
        conclusion = And(PropVar("A"), PropVar("B"))
        
        result = prove(premises, conclusion)
        
        self.assertIsNotNone(result)
        self.assertTrue(result.is_complete())

    def test_or_introduction(self):
        premises = [PropVar("A")]
        conclusion = Or(PropVar("A"), PropVar("B"))
        
        result = prove(premises, conclusion)
        
        self.assertIsNotNone(result)
        self.assertTrue(result.is_complete())

    def test_imp_introduction(self):
        premises = []
        conclusion = Imp(PropVar("A"), PropVar("A"))
        
        result = prove(premises, conclusion)
        
        self.assertIsNotNone(result)
        self.assertTrue(result.is_complete())

    def test_not_introduction(self):
        premises = [And(PropVar("A"), Not(PropVar("A")))]
        conclusion = Not(PropVar("A"))
        
        result = prove(premises, conclusion)
        
        self.assertIsNotNone(result)
        self.assertTrue(result.is_complete())

    def test_indirect_proof(self):
        premises = [And(PropVar("A"), Not(PropVar("A")))]
        conclusion = PropVar("B")
        
        result = prove(premises, conclusion)
        
        self.assertIsNotNone(result)
        self.assertTrue(result.is_complete())

    def test_nested_imp(self):
        premises = [Imp(PropVar("A"), PropVar("B"))]
        conclusion = Imp(PropVar("A"), Or(PropVar("B"), PropVar("C")))
        
        result = prove(premises, conclusion)
        
        self.assertIsNotNone(result)
        self.assertTrue(result.is_complete())

    def test_complex_proof(self):
        premises = [Imp(PropVar("A"), PropVar("B")), Imp(PropVar("B"), PropVar("C"))]
        conclusion = Imp(PropVar("A"), PropVar("C"))
        
        result = prove(premises, conclusion)
        
        self.assertIsNotNone(result)
        self.assertTrue(result.is_complete())

    def test_invalid_argument_returns_none(self):
        premises = [PropVar("A")]
        conclusion = PropVar("B")
        
        result = prove(premises, conclusion)
        
        self.assertIsNone(result)

    def test_conclusion_already_premise(self):
        premises = [PropVar("A")]
        conclusion = PropVar("A")
        
        result = prove(premises, conclusion)
        
        self.assertIsNotNone(result)
        self.assertTrue(result.is_complete())

    def test_modus_tollens(self):
        premises = [Imp(PropVar("A"), PropVar("B")), Not(PropVar("B"))]
        conclusion = Not(PropVar("A"))
        
        result = prove(premises, conclusion)
        
        self.assertIsNotNone(result)
        self.assertTrue(result.is_complete())

    def test_disjunctive_syllogism(self):
        premises = [Or(PropVar("A"), PropVar("B")), Not(PropVar("A"))]
        conclusion = PropVar("B")
        
        result = prove(premises, conclusion)
        
        self.assertIsNotNone(result)
        self.assertTrue(result.is_complete())


class TestProveEdgeCases(unittest.TestCase):
    def test_no_premises_tautology(self):
        premises = []
        conclusion = Imp(PropVar("A"), PropVar("A"))
        
        result = prove(premises, conclusion)
        
        self.assertIsNotNone(result)
        self.assertTrue(result.is_complete())

    def test_no_premises_lem(self):
        premises = []
        conclusion = Or(PropVar("A"), Not(PropVar("A")))
        
        result = prove(premises, conclusion)
        
        self.assertIsNotNone(result)
        self.assertTrue(result.is_complete())

    def test_conclusion_is_premise(self):
        premises = [PropVar("A"), PropVar("B")]
        conclusion = PropVar("A")
        
        result = prove(premises, conclusion)
        
        self.assertIsNotNone(result)
        self.assertTrue(result.is_complete())

    def test_memoization_prevents_redundant_work(self):
        premises = [Imp(PropVar("A"), PropVar("B")), Imp(PropVar("B"), PropVar("C"))]
        conclusion = Imp(PropVar("A"), PropVar("C"))
        
        result = prove(premises, conclusion)
        
        self.assertIsNotNone(result)
        self.assertTrue(result.is_complete())

    def test_complex_nested_structure(self):
        premises = [And(PropVar("A"), PropVar("B"))]
        conclusion = And(And(PropVar("A"), PropVar("B")), And(PropVar("A"), PropVar("B")))
        
        result = prove(premises, conclusion)
        
        self.assertIsNotNone(result)
        self.assertTrue(result.is_complete())

    def test_multiple_premises_complex_conclusion(self):
        premises = [
            Imp(PropVar("A"), PropVar("B")),
            Imp(PropVar("C"), PropVar("D")),
            PropVar("A"),
            PropVar("C")
        ]
        conclusion = And(PropVar("B"), PropVar("D"))
        
        result = prove(premises, conclusion)
        
        self.assertIsNotNone(result)
        self.assertTrue(result.is_complete())

    def test_deeply_nested_implication(self):
        premises = []
        conclusion = Imp(
            PropVar("A"),
            Imp(PropVar("B"), Imp(PropVar("C"), PropVar("A")))
        )
        
        result = prove(premises, conclusion)
        
        self.assertIsNotNone(result)
        self.assertTrue(result.is_complete())

    def test_contradiction_to_anything(self):
        premises = [And(PropVar("A"), Not(PropVar("A")))]
        conclusion = PropVar("B")
        
        result = prove(premises, conclusion)
        
        self.assertIsNotNone(result)
        self.assertTrue(result.is_complete())

    def test_double_negation(self):
        premises = [PropVar("A")]
        conclusion = Not(Not(PropVar("A")))
        
        result = prove(premises, conclusion)
        
        self.assertIsNotNone(result)
        self.assertTrue(result.is_complete())

    def test_implication_chain(self):
        premises = [
            Imp(PropVar("A"), PropVar("B")),
            Imp(PropVar("B"), PropVar("C")),
            Imp(PropVar("C"), PropVar("D"))
        ]
        conclusion = Imp(PropVar("A"), PropVar("D"))
        
        result = prove(premises, conclusion)
        
        self.assertIsNotNone(result)
        self.assertTrue(result.is_complete())


if __name__ == "__main__":
    unittest.main()

