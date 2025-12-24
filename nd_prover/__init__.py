__version__ = "2.0.0"
__author__ = "Daniyal Akif"
__email__ = "daniyalakif@gmail.com"
__license__ = "MIT"
__description__ = "Natural deduction proof generator & checker"
__url__ = "https://github.com/daniyal1249/nd-prover"


from .cli import (
    logics, parse_and_verify_formula, parse_and_verify_premises, 
    select_logic, input_premises, input_conclusion, create_problem, 
    select_edit, input_line, input_assumption, perform_edit, main
)
from .logic import (
    InferenceError, ProofEditError, Metavar, Formula, Bot, Not, And, Or, 
    Imp, Iff, Term, Func, Var, Pred, Eq, Forall, Exists, Box, Dia, 
    BoxMarker, Rule, Justification, Rules, verify_arity, 
    assumption_constants, TFL, FOL, MLK, MLT, MLS4, MLS5, FOMLK, FOMLT, 
    FOMLS4, FOMLS5, is_tfl_formula, is_fol_formula, is_fol_sentence, 
    is_ml_formula, atomic_terms, constants, free_vars, sub_term, 
    ProofObject, Line, Proof, Problem
)
from .parser import (
    ParsingError, Symbols, split_line, strip_parens, find_main_connective, 
    split_args, parse_args_from_parens, parse_term, _parse_formula, 
    parse_formula, parse_assumption, parse_rule, parse_citations, 
    parse_justification, parse_line
)
from .prover import (
    ProverError, _ProofObject, _Line, _Proof, Eliminator, Introducer, 
    Prover, Processor, prove
)
from .tfl_sat import prop_vars, evaluate, is_valid


__all__ = [name for name in globals() if not name.startswith("__")]
