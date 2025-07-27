import unittest

from parser import *


class TestParseFormula(unittest.TestCase):
    def test_propvar(self):
        self.assertEqual(parse_formula('A'), PropVar('A'))
        self.assertEqual(parse_formula('X'), PropVar('X'))

    def test_pred(self):
        self.assertEqual(parse_formula('Pb'), Pred('P', 'b'))
        self.assertEqual(parse_formula('Fcdc'), Pred('F', 'cdc'))
        self.assertEqual(parse_formula('Kxy'), Pred('K', 'xy'))

    def test_forall_exists(self):
        self.assertEqual(parse_formula('forallzPz'), Forall('z', Pred('P', 'z')))
        self.assertEqual(parse_formula('∀sPs'), Forall('s', Pred('P', 's')))
        self.assertEqual(parse_formula('existszLz'), Exists('z', Pred('L', 'z')))
        self.assertEqual(parse_formula('∃yPy'), Exists('y', Pred('P', 'y')))

    def test_equality(self):
        self.assertEqual(parse_formula('a=b'), Eq('a', 'b'))
        self.assertEqual(parse_formula('k = m'), Eq('k', 'm'))
        with self.assertRaises(ParsingError):
            parse_formula('ab=c')
        with self.assertRaises(ParsingError):
            parse_formula('a=bc')
        with self.assertRaises(ParsingError):
            parse_formula('B=c')

    def test_falsum(self):
        self.assertEqual(parse_formula('falsum'), Falsum())
        self.assertEqual(parse_formula('⊥'), Falsum())
        self.assertEqual(parse_formula('XX'), Falsum())
        self.assertEqual(parse_formula('#'), Falsum())

    def test_not(self):
        self.assertEqual(parse_formula('~A'), Not(PropVar('A')))
        self.assertEqual(parse_formula('¬A'), Not(PropVar('A')))
        self.assertEqual(parse_formula('-B'), Not(PropVar('B')))
        self.assertEqual(parse_formula('¬Pb'), Not(Pred('P', 'b')))

    def test_and(self):
        self.assertEqual(parse_formula('A and B'), And(PropVar('A'), PropVar('B')))
        self.assertEqual(parse_formula('(A ∧ B)'), And(PropVar('A'), PropVar('B')))
        self.assertEqual(parse_formula('A&B'), And(PropVar('A'), PropVar('B')))
        self.assertEqual(parse_formula('A*B'), And(PropVar('A'), PropVar('B')))

    def test_or(self):
        self.assertEqual(parse_formula('A or B'), Or(PropVar('A'), PropVar('B')))
        self.assertEqual(parse_formula('(A∨B)'), Or(PropVar('A'), PropVar('B')))

    def test_imp(self):
        self.assertEqual(parse_formula('A -> B'), Imp(PropVar('A'), PropVar('B')))
        self.assertEqual(parse_formula('A⇒B'), Imp(PropVar('A'), PropVar('B')))
        self.assertEqual(parse_formula('A⊃B'), Imp(PropVar('A'), PropVar('B')))
        self.assertEqual(parse_formula('A> B'), Imp(PropVar('A'), PropVar('B')))
        self.assertEqual(parse_formula('(A→B)'), Imp(PropVar('A'), PropVar('B')))

    def test_iff(self):
        self.assertEqual(parse_formula('A <-> B'), Iff(PropVar('A'), PropVar('B')))
        self.assertEqual(parse_formula('A↔B'), Iff(PropVar('A'), PropVar('B')))
        self.assertEqual(parse_formula('A≡B'), Iff(PropVar('A'), PropVar('B')))

    def test_box_dia(self):
        self.assertEqual(parse_formula('boxA'), Box(PropVar('A')))
        self.assertEqual(parse_formula('[]A'), Box(PropVar('A')))
        self.assertEqual(parse_formula('□A'), Box(PropVar('A')))
        self.assertEqual(parse_formula('diaB'), Dia(PropVar('B')))
        self.assertEqual(parse_formula('<>C'), Dia(PropVar('C')))
        self.assertEqual(parse_formula('♢C'), Dia(PropVar('C')))

    def test_compound(self):
        self.assertEqual(
            parse_formula('(A and (B or C))'),
            And(PropVar('A'), Or(PropVar('B'), PropVar('C')))
        )
        self.assertEqual(
            parse_formula('¬(A→(B∧C))'),
            Not(Imp(PropVar('A'), And(PropVar('B'), PropVar('C'))))
        )
        self.assertEqual(
            parse_formula('(A∧B)→(C∨¬D)'),
            Imp(And(PropVar('A'), PropVar('B')), Or(PropVar('C'), Not(PropVar('D'))))
        )
        self.assertEqual(
            parse_formula('∀x(Px→Qx)'),
            Forall('x', Imp(Pred('P', 'x'), Pred('Q', 'x')))
        )
        self.assertEqual(
            parse_formula('□(A↔¬B)'),
            Box(Iff(PropVar('A'), Not(PropVar('B'))))
        )
        self.assertEqual(
            parse_formula('¬¬A'),
            Not(Not(PropVar('A')))
        )

    def test_strip_parens(self):
        self.assertEqual(parse_formula('(((A)))'), PropVar('A'))
        self.assertEqual(parse_formula('((A∧B))'), And(PropVar('A'), PropVar('B')))

    def test_invalid(self):
        with self.assertRaises(ParsingError):
            parse_formula('A=')
        with self.assertRaises(ParsingError):
            parse_formula('')
        with self.assertRaises(ParsingError):
            parse_formula('()')
        with self.assertRaises(ParsingError):
            parse_formula('AB')
        with self.assertRaises(ParsingError):
            parse_formula('A∧')
        with self.assertRaises(ParsingError):
            parse_formula('∀APa')


if __name__ == '__main__':
    unittest.main()