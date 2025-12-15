from .parser import *


logics = {
    "TFL": TFL,
    "FOL": FOL,
    "MLK": MLK,
    "MLT": MLT,
    "MLS4": MLS4,
    "MLS5": MLS5,
}


def parse_and_verify_formula(f, logic):
    f = parse_formula(f)
    if logic is TFL and is_tfl_formula(f):
        return f
    if logic is FOL and is_fol_formula(f):
        return f
    if issubclass(logic, MLK) and is_ml_formula(f):
        return f
    raise ParsingError(f'"{f}" is not a valid {logic.__name__} formula.')


def parse_and_verify_premises(s, logic):
    s = s.strip()
    if s == "NA":
        return []
    parts = [p for p in s.split(";") if p.strip()]
    return [parse_and_verify_formula(p, logic) for p in parts]


def select_logic():
    while True:
        raw = input(f"Select logic ({', '.join(logics)}): ")
        logic = logics.get(raw.strip().upper())
        if logic is not None:
            return logic
        print("Invalid logic. Please try again.")


def input_premises(logic):
    while True:
        raw = input('Enter premises (separated by ";"), or "NA" if none: ')
        try:
            return parse_and_verify_premises(raw, logic)
        except ParsingError as e:
            print(f"{e} Please try again.")


def input_conclusion(logic):
    while True:
        raw = input("Enter conclusion: ")
        try:
            return parse_and_verify_formula(raw, logic)
        except ParsingError as e:
            print(f"{e} Please try again.")


def create_problem():
    logic = select_logic()
    premises = input_premises(logic)
    conclusion = input_conclusion(logic)
    return Proof(logic, premises, conclusion)


def select_action():
    actions = [
        "1 - Add a new line",
        "2 - Begin a new subproof",
        "3 - End the current subproof",
        "4 - End the current subproof and begin a new one",
        "5 - Delete the last line",
    ]

    while True:
        raw = input("\n".join(actions) + "\n\nSelect action: ")
        if raw.strip().isdecimal() and 1 <= int(raw) <= 5:
            return int(raw)
        print("Invalid action. Please try again.\n")


def input_line():
    raw = input("Enter line: ")
    return parse_line(raw)


def input_assumption():
    raw = input("Enter assumption: ")
    return parse_assumption(raw)


def perform_action(proof, action):
    try:
        match action:
            case 1:
                f, j = input_line()
                proof.add_line(f, j)
            case 2:
                a = input_assumption()
                proof.begin_subproof(a)
            case 3:
                f, j = input_line()
                proof.end_subproof(f, j)
            case 4:
                a = input_assumption()
                proof.end_and_begin_subproof(a)
            case 5:
                proof.delete_line()
    except Exception as e:
        print(f"{e} Please try again.")


def main():
    p = create_problem()
    while not p.is_complete():
        print()
        if p_str := str(p):
            print(f"{p_str}\n")
        action = select_action()
        perform_action(p, action)

    print(f"\n{p}\n")
    print("Proof complete! 🎉")
