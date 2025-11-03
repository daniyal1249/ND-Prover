import unittest
import time

from nd_prover import *
from nd_prover.tfl_semantic import prop_vars, evaluate, is_valid


class TestPropVars(unittest.TestCase):
    def test_propvar(self):
        self.assertEqual(prop_vars(PropVar("A")), {"A"})
        self.assertEqual(prop_vars(PropVar("P")), {"P"})

    def test_falsum(self):
        self.assertEqual(prop_vars(Falsum()), set())

    def test_not(self):
        self.assertEqual(prop_vars(Not(PropVar("A"))), {"A"})
        self.assertEqual(prop_vars(Not(Falsum())), set())
        self.assertEqual(prop_vars(Not(Not(PropVar("B")))), {"B"})

    def test_binary_connectives(self):
        self.assertEqual(prop_vars(And(PropVar("A"), PropVar("B"))), {"A", "B"})
        self.assertEqual(prop_vars(Or(PropVar("P"), PropVar("Q"))), {"P", "Q"})
        self.assertEqual(prop_vars(Imp(PropVar("X"), PropVar("Y"))), {"X", "Y"})
        self.assertEqual(prop_vars(Iff(PropVar("P"), PropVar("Q"))), {"P", "Q"})

    def test_duplicate_vars(self):
        self.assertEqual(prop_vars(And(PropVar("A"), PropVar("A"))), {"A"})
        self.assertEqual(prop_vars(Or(PropVar("P"), And(PropVar("P"), PropVar("Q")))), {"P", "Q"})

    def test_nested(self):
        formula = Imp(And(PropVar("A"), PropVar("B")), Or(PropVar("C"), Not(PropVar("D"))))
        self.assertEqual(prop_vars(formula), {"A", "B", "C", "D"})

    def test_no_vars(self):
        self.assertEqual(prop_vars(And(Falsum(), Falsum())), set())
        self.assertEqual(prop_vars(Not(Not(Falsum()))), set())


class TestEvaluate(unittest.TestCase):
    def test_falsum(self):
        self.assertFalse(evaluate(Falsum(), {}))
        self.assertFalse(evaluate(Falsum(), {"A": True}))

    def test_propvar(self):
        self.assertTrue(evaluate(PropVar("A"), {"A": True}))
        self.assertFalse(evaluate(PropVar("A"), {"A": False}))
        self.assertTrue(evaluate(PropVar("P"), {"P": True, "Q": False}))

    def test_not(self):
        self.assertTrue(evaluate(Not(PropVar("A")), {"A": False}))
        self.assertFalse(evaluate(Not(PropVar("A")), {"A": True}))
        self.assertTrue(evaluate(Not(Not(PropVar("P"))), {"P": True}))

    def test_and(self):
        self.assertTrue(evaluate(And(PropVar("A"), PropVar("B")), {"A": True, "B": True}))
        self.assertFalse(evaluate(And(PropVar("A"), PropVar("B")), {"A": True, "B": False}))
        self.assertFalse(evaluate(And(PropVar("A"), PropVar("B")), {"A": False, "B": True}))
        self.assertFalse(evaluate(And(PropVar("A"), PropVar("B")), {"A": False, "B": False}))

    def test_or(self):
        self.assertTrue(evaluate(Or(PropVar("A"), PropVar("B")), {"A": True, "B": True}))
        self.assertTrue(evaluate(Or(PropVar("A"), PropVar("B")), {"A": True, "B": False}))
        self.assertTrue(evaluate(Or(PropVar("A"), PropVar("B")), {"A": False, "B": True}))
        self.assertFalse(evaluate(Or(PropVar("A"), PropVar("B")), {"A": False, "B": False}))

    def test_imp(self):
        self.assertTrue(evaluate(Imp(PropVar("A"), PropVar("B")), {"A": True, "B": True}))
        self.assertFalse(evaluate(Imp(PropVar("A"), PropVar("B")), {"A": True, "B": False}))
        self.assertTrue(evaluate(Imp(PropVar("A"), PropVar("B")), {"A": False, "B": True}))
        self.assertTrue(evaluate(Imp(PropVar("A"), PropVar("B")), {"A": False, "B": False}))

    def test_iff(self):
        self.assertTrue(evaluate(Iff(PropVar("A"), PropVar("B")), {"A": True, "B": True}))
        self.assertFalse(evaluate(Iff(PropVar("A"), PropVar("B")), {"A": True, "B": False}))
        self.assertFalse(evaluate(Iff(PropVar("A"), PropVar("B")), {"A": False, "B": True}))
        self.assertTrue(evaluate(Iff(PropVar("A"), PropVar("B")), {"A": False, "B": False}))

    def test_nested(self):
        formula = Imp(And(PropVar("A"), PropVar("B")), Or(PropVar("A"), PropVar("C")))
        self.assertTrue(evaluate(formula, {"A": True, "B": True, "C": False}))
        self.assertTrue(evaluate(formula, {"A": True, "B": False, "C": False}))
        self.assertTrue(evaluate(formula, {"A": False, "B": True, "C": False}))
        
        formula2 = Imp(And(PropVar("A"), PropVar("B")), And(PropVar("C"), PropVar("D")))
        self.assertFalse(evaluate(formula2, {"A": True, "B": True, "C": True, "D": False}))
        self.assertTrue(evaluate(formula2, {"A": True, "B": True, "C": True, "D": True}))

    def test_falsum_in_formulas(self):
        self.assertFalse(evaluate(And(Falsum(), PropVar("A")), {"A": True}))
        self.assertTrue(evaluate(Or(Falsum(), PropVar("A")), {"A": True}))
        self.assertTrue(evaluate(Imp(Falsum(), PropVar("A")), {"A": True}))


class TestIsValid(unittest.TestCase):
    def test_modus_ponens(self):
        premise = Imp(PropVar("P"), PropVar("Q"))
        premises = [premise, PropVar("P")]
        conclusion = PropVar("Q")
        self.assertTrue(is_valid(premises, conclusion))

    def test_modus_tollens(self):
        premise1 = Imp(PropVar("P"), PropVar("Q"))
        premise2 = Not(PropVar("Q"))
        premises = [premise1, premise2]
        conclusion = Not(PropVar("P"))
        self.assertTrue(is_valid(premises, conclusion))

    def test_hypothetical_syllogism(self):
        premise1 = Imp(PropVar("P"), PropVar("Q"))
        premise2 = Imp(PropVar("Q"), PropVar("R"))
        premises = [premise1, premise2]
        conclusion = Imp(PropVar("P"), PropVar("R"))
        self.assertTrue(is_valid(premises, conclusion))

    def test_disjunctive_syllogism(self):
        premise1 = Or(PropVar("P"), PropVar("Q"))
        premise2 = Not(PropVar("P"))
        premises = [premise1, premise2]
        conclusion = PropVar("Q")
        self.assertTrue(is_valid(premises, conclusion))

    def test_and_introduction(self):
        premises = [PropVar("P"), PropVar("Q")]
        conclusion = And(PropVar("P"), PropVar("Q"))
        self.assertTrue(is_valid(premises, conclusion))

    def test_or_introduction(self):
        premises = [PropVar("P")]
        conclusion = Or(PropVar("P"), PropVar("Q"))
        self.assertTrue(is_valid(premises, conclusion))

    def test_contraposition(self):
        premise = Imp(PropVar("P"), PropVar("Q"))
        premises = [premise]
        conclusion = Imp(Not(PropVar("Q")), Not(PropVar("P")))
        self.assertTrue(is_valid(premises, conclusion))

    def test_invalid_argument(self):
        premises = [PropVar("P")]
        conclusion = PropVar("Q")
        self.assertFalse(is_valid(premises, conclusion))

    def test_affirming_consequent(self):
        premise1 = Imp(PropVar("P"), PropVar("Q"))
        premise2 = PropVar("Q")
        premises = [premise1, premise2]
        conclusion = PropVar("P")
        self.assertFalse(is_valid(premises, conclusion))

    def test_denying_antecedent(self):
        premise1 = Imp(PropVar("P"), PropVar("Q"))
        premise2 = Not(PropVar("P"))
        premises = [premise1, premise2]
        conclusion = Not(PropVar("Q"))
        self.assertFalse(is_valid(premises, conclusion))

    def test_no_premises(self):
        premises = []
        conclusion = Or(PropVar("P"), Not(PropVar("P")))
        self.assertTrue(is_valid(premises, conclusion))

    def test_no_premises_invalid(self):
        premises = []
        conclusion = PropVar("P")
        self.assertFalse(is_valid(premises, conclusion))

    def test_no_variables(self):
        premises = [Falsum()]
        conclusion = Falsum()
        self.assertTrue(is_valid(premises, conclusion))

    def test_no_variables_invalid(self):
        premises = []
        conclusion = Falsum()
        self.assertFalse(is_valid(premises, conclusion))

    def test_multiple_premises(self):
        premises = [PropVar("P"), PropVar("Q"), PropVar("R")]
        conclusion = And(And(PropVar("P"), PropVar("Q")), PropVar("R"))
        self.assertTrue(is_valid(premises, conclusion))

    def test_complex_nested_valid(self):
        premise1 = Imp(And(PropVar("A"), PropVar("B")), PropVar("C"))
        premise2 = PropVar("A")
        premise3 = PropVar("B")
        premises = [premise1, premise2, premise3]
        conclusion = PropVar("C")
        self.assertTrue(is_valid(premises, conclusion))

    def test_complex_nested_invalid(self):
        premise1 = Imp(And(PropVar("A"), PropVar("B")), PropVar("C"))
        premise2 = PropVar("A")
        premises = [premise1, premise2]
        conclusion = PropVar("C")
        self.assertFalse(is_valid(premises, conclusion))

    def test_tautology_premise(self):
        premises = [Or(PropVar("P"), Not(PropVar("P")))]
        conclusion = PropVar("Q")
        self.assertFalse(is_valid(premises, conclusion))

    def test_contradiction_premise(self):
        premises = [And(PropVar("P"), Not(PropVar("P")))]
        conclusion = PropVar("Q")
        self.assertTrue(is_valid(premises, conclusion))

    def test_efficiency_early_exit(self):
        premise = PropVar("P")
        premises = [premise]
        conclusion = PropVar("Q")
        
        start = time.time()
        result = is_valid(premises, conclusion)
        elapsed = time.time() - start
        
        self.assertFalse(result)
        self.assertLess(elapsed, 0.1)

    def test_efficiency_large_valid(self):
        premises = [PropVar("A"), PropVar("B"), PropVar("C"), PropVar("D"), PropVar("E")]
        conclusion = And(And(And(And(PropVar("A"), PropVar("B")), PropVar("C")), PropVar("D")), PropVar("E"))
        
        start = time.time()
        result = is_valid(premises, conclusion)
        elapsed = time.time() - start
        
        self.assertTrue(result)
        self.assertLess(elapsed, 1.0)

    def test_three_variables(self):
        premises = [Imp(PropVar("P"), PropVar("Q")), Imp(PropVar("Q"), PropVar("R"))]
        conclusion = Imp(PropVar("P"), PropVar("R"))
        self.assertTrue(is_valid(premises, conclusion))

    def test_four_variables(self):
        premises = [Imp(And(PropVar("A"), PropVar("B")), PropVar("C")), PropVar("A"), PropVar("B"), PropVar("D")]
        conclusion = PropVar("C")
        self.assertTrue(is_valid(premises, conclusion))


if __name__ == "__main__":
    unittest.main()
