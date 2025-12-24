from dataclasses import dataclass

from .tfl_sat import *


class ProverError(Exception):
    pass


class _ProofObject:
    count = 0

    def __init__(self):
        type(self).count += 1
        self.id = type(self).count

    def is_line(self):
        return isinstance(self, _Line)
    
    def is_subproof(self):
        return isinstance(self, _Proof)


@dataclass
class _Line(_ProofObject):
    formula: Formula
    rule: str
    citations: tuple

    def __post_init__(self):
        super().__init__()


@dataclass
class _Proof(_ProofObject):
    seq: list[_ProofObject]
    goal: Formula

    def __post_init__(self):
        self.seq = self.seq[:]
        super().__init__()

    def copy(self):
        return _Proof(self.seq, self.goal)

    def assumptions(self):
        return {
            obj.formula 
            for obj in self.seq 
            if obj.is_line() and obj.rule in ("PR", "AS")
        }

    def citations(self):
        c_set = set()
        for obj in self.seq:
            if obj.is_line():
                c_set.update(obj.citations)
            else:
                c_set.update(obj.citations())
        return c_set

    def line_count(self):
        return sum(
            1 if obj.is_line() else obj.line_count() 
            for obj in self.seq
        )

    def ip_count(self):
        return sum(
            (1 if obj.rule == "IP" else 0) 
            if obj.is_line() else obj.ip_count() 
            for obj in self.seq
        )

    def pop_reiteration(self):
        end = self.seq[-1]
        if end.is_line() and end.rule == "R":
            self.seq.pop()
            return end.citations[0]
        return end.id

    def commit_best_branch(self, branches):
        if not branches:
            return False
        def key(p): return (p.ip_count(), p.line_count())
        self.seq = min(branches, key=key).seq
        return True


class Eliminator:

    @staticmethod
    def elim(prover):
        while True:
            if Eliminator.R(prover):
                return True
            if Eliminator.X(prover):
                return True
            if Eliminator.NotE(prover):
                continue
            if Eliminator.AndE(prover):
                continue
            if Eliminator.ImpE(prover):
                continue
            if Eliminator.IffE(prover):
                continue
            return False

    @staticmethod
    def R(prover):
        proof = prover.proof
        if proof.seq and (end := proof.seq[-1]).is_line():
            if end.formula == proof.goal and end.rule not in ("PR", "AS"):
                return True

        for obj in proof.seq:
            if obj.is_line() and obj.formula == proof.goal:
                line = _Line(obj.formula, "R", (obj.id,))
                proof.seq.append(line)
                return True
        return False

    @staticmethod
    def X(prover):
        proof = prover.proof
        for obj in proof.seq:
            if obj.is_line() and isinstance(obj.formula, Bot):
                line = _Line(proof.goal, "X", (obj.id,))
                proof.seq.append(line)
                return True
        return False

    @staticmethod
    def NotE(prover):
        proof = prover.proof
        for obj in proof.seq:
            if not (obj.is_line() and isinstance(obj.formula, Not)):
                continue
            for obj2 in proof.seq:
                if obj2.is_line() and obj2.formula == obj.formula.inner:
                    line = _Line(Bot(), "¬E", (obj.id, obj2.id))
                    proof.seq.append(line)
                    return True
        return False

    @staticmethod
    def AndE(prover):
        proof = prover.proof
        formulas = {obj.formula for obj in proof.seq if obj.is_line()}

        for obj in proof.seq:
            if not (obj.is_line() and isinstance(obj.formula, And)):
                continue
            for conjunct in (obj.formula.left, obj.formula.right):
                if conjunct not in formulas:
                    line = _Line(conjunct, "∧E", (obj.id,))
                    proof.seq.append(line)
                    return True
        return False

    @staticmethod
    def ImpE(prover):
        proof = prover.proof
        formulas = {obj.formula for obj in proof.seq if obj.is_line()}

        for obj in proof.seq:
            if not (obj.is_line() and isinstance(obj.formula, Imp)):
                continue
            if obj.formula.right in formulas:
                continue
            for obj2 in proof.seq:
                if obj2.is_line() and obj2.formula == obj.formula.left:
                    line = _Line(obj.formula.right, "→E", (obj.id, obj2.id))
                    proof.seq.append(line)
                    return True
        return False

    @staticmethod
    def IffE(prover):
        proof = prover.proof
        formulas = {obj.formula for obj in proof.seq if obj.is_line()}

        for obj in proof.seq:
            if not (obj.is_line() and isinstance(obj.formula, Iff)):
                continue
            have_left = obj.formula.left in formulas
            have_right = obj.formula.right in formulas

            if have_left and not have_right:
                for obj2 in proof.seq:
                    if obj2.is_line() and obj2.formula == obj.formula.left:
                        line = _Line(obj.formula.right, "↔E", (obj.id, obj2.id))
                        proof.seq.append(line)
                        return True

            if have_right and not have_left:
                for obj2 in proof.seq:
                    if obj2.is_line() and obj2.formula == obj.formula.right:
                        line = _Line(obj.formula.left, "↔E", (obj.id, obj2.id))
                        proof.seq.append(line)
                        return True
        return False

    @staticmethod
    def OrE(prover):
        proof = prover.proof
        goal = proof.goal
        branches = []
        n = len(proof.seq)

        for obj in proof.seq:
            if not (obj.is_line() and isinstance(obj.formula, Or)):
                continue
            disjunct1, disjunct2 = obj.formula.left, obj.formula.right

            assumption1 = _Line(disjunct1, "AS", ())
            subproof1 = _Proof(proof.seq + [assumption1], goal)
            p1 = Prover(subproof1, prover.seen.copy())
            if not p1.prove():
                continue
            subproof1.seq = subproof1.seq[n:]

            assumption2 = _Line(disjunct2, "AS", ())
            subproof2 = _Proof(proof.seq + [subproof1, assumption2], goal)
            p2 = Prover(subproof2, prover.seen.copy())
            if not p2.prove():
                continue
            subproof2.seq = subproof2.seq[n + 1:]

            line = _Line(goal, "∨E", (obj.id, subproof1.id, subproof2.id))
            branch = _Proof(proof.seq + [subproof1, subproof2, line], goal)
            branches.append(branch)

        return proof.commit_best_branch(branches)

    @staticmethod
    def NotE_force(prover):
        proof = prover.proof
        branches = []
        if not is_valid(proof.assumptions(), Bot()):
            return False
        
        for obj in proof.seq:
            if obj.is_line() and isinstance(obj.formula, Not):
                branch = _Proof(proof.seq, obj.formula.inner)
                p = Prover(branch, prover.seen)
                if p.prove():
                    branch.pop_reiteration()
                    if branch.seq != proof.seq:
                        branches.append(branch)

        return proof.commit_best_branch(branches)

    @staticmethod
    def ImpE_force(prover):
        proof = prover.proof
        formulas = {obj.formula for obj in proof.seq if obj.is_line()}

        for obj in proof.seq:
            if not (obj.is_line() and isinstance(obj.formula, Imp)):
                continue
            if obj.formula.right in formulas:
                continue

            if is_valid(proof.assumptions(), obj.formula.left):
                branch = _Proof(proof.seq, obj.formula.left)
                p = Prover(branch, prover.seen)
                if p.prove():
                    branch.pop_reiteration()
                    if branch.seq != proof.seq:
                        proof.seq = branch.seq
                        return True
        return False

    @staticmethod
    def IffE_force(prover):
        proof = prover.proof
        formulas = {obj.formula for obj in proof.seq if obj.is_line()}

        for obj in proof.seq:
            if not (obj.is_line() and isinstance(obj.formula, Iff)):
                continue
            if obj.formula.left in formulas or obj.formula.right in formulas:
                continue
            if not is_valid(proof.assumptions(), obj.formula.left):
                continue

            branches = []
            for formula in (obj.formula.left, obj.formula.right):
                branch = _Proof(proof.seq, formula)
                p = Prover(branch, prover.seen.copy())
                if p.prove():
                    branch.pop_reiteration()
                    if branch.seq != proof.seq:
                        branches.append(branch)

            if proof.commit_best_branch(branches):
                return True
        return False


class Introducer:

    @staticmethod
    def intro(prover):
        match prover.proof.goal:
            case Not():
                return Introducer.NotI(prover)
            case And():
                return Introducer.AndI(prover)
            case Or():
                return Introducer.OrI(prover)
            case Imp():
                return Introducer.ImpI(prover)
            case Iff():
                return Introducer.IffI(prover)
        return False

    @staticmethod
    def NotI(prover):
        proof = prover.proof
        assumption = _Line(proof.goal.inner, "AS", ())
        subproof = _Proof(proof.seq + [assumption], Bot())
        p = Prover(subproof, prover.seen)
        if not p.prove():
            return False
        
        n = len(proof.seq)
        subproof.seq = subproof.seq[n:]
        proof.seq.append(subproof)
        line = _Line(proof.goal, "¬I", (subproof.id,))
        proof.seq.append(line)
        return True

    @staticmethod
    def AndI(prover):
        proof = prover.proof
        left, right = proof.goal.left, proof.goal.right
        branches = []

        for conjunct1, conjunct2 in [(left, right), (right, left)]:
            branch1 = _Proof(proof.seq, conjunct1)
            p1 = Prover(branch1, prover.seen.copy())
            if not p1.prove():
                continue
            conjunct1_id = branch1.pop_reiteration()

            branch2 = _Proof(branch1.seq, conjunct2)
            p2 = Prover(branch2, prover.seen.copy())
            if not p2.prove():
                continue
            conjunct2_id = branch2.pop_reiteration()
            
            line = _Line(proof.goal, "∧I", (conjunct1_id, conjunct2_id))
            branch2.seq.append(line)
            branches.append(branch2)

        return proof.commit_best_branch(branches)

    @staticmethod
    def OrI(prover):
        proof = prover.proof
        left, right = proof.goal.left, proof.goal.right
        branches = []

        # For efficiency
        for obj in proof.seq:
            if obj.is_line() and obj.formula in (left, right):
                line = _Line(proof.goal, "∨I", (obj.id,))
                proof.seq.append(line)
                return True
        
        for disjunct in (left, right):
            if is_valid(proof.assumptions(), disjunct):
                branch = _Proof(proof.seq, disjunct)
                p = Prover(branch, prover.seen)
                if p.prove():
                    disjunct_id = branch.pop_reiteration()
                    line = _Line(proof.goal, "∨I", (disjunct_id,))
                    branch.seq.append(line)
                    branches.append(branch)

        return proof.commit_best_branch(branches)

    @staticmethod
    def ImpI(prover):
        proof = prover.proof
        assumption = _Line(proof.goal.left, "AS", ())
        subproof = _Proof(proof.seq + [assumption], proof.goal.right)
        p = Prover(subproof, prover.seen)
        if not p.prove():
            return False
        
        n = len(proof.seq)
        subproof.seq = subproof.seq[n:]
        proof.seq.append(subproof)
        line = _Line(proof.goal, "→I", (subproof.id,))
        proof.seq.append(line)
        return True

    @staticmethod
    def IffI(prover):
        proof = prover.proof
        left, right = proof.goal.left, proof.goal.right
        n = len(proof.seq)

        assumption1 = _Line(left, "AS", ())
        subproof1 = _Proof(proof.seq + [assumption1], right)
        p1 = Prover(subproof1, prover.seen.copy())
        if not p1.prove():
            return False
        subproof1.seq = subproof1.seq[n:]

        assumption2 = _Line(right, "AS", ())
        subproof2 = _Proof(proof.seq + [subproof1, assumption2], left)
        p2 = Prover(subproof2, prover.seen.copy())
        if not p2.prove():
            return False
        subproof2.seq = subproof2.seq[n + 1:]

        proof.seq.extend((subproof1, subproof2))
        line = _Line(proof.goal, "↔I", (subproof1.id, subproof2.id))
        proof.seq.append(line)
        return True

    @staticmethod
    def IP(prover):
        proof = prover.proof
        assumption = _Line(Not(proof.goal), "AS", ())
        subproof = _Proof(proof.seq + [assumption], Bot())
        p = Prover(subproof, prover.seen)
        if not p.prove():
            return False
        
        n = len(proof.seq)
        subproof.seq = subproof.seq[n:]
        proof.seq.append(subproof)
        line = _Line(proof.goal, "IP", (subproof.id,))
        proof.seq.append(line)
        return True


class Prover:

    def __init__(self, proof, seen=None):
        self.proof = proof
        self.seen = {} if seen is None else seen

    def prove(self):
        if not self._enter_state():
            return False

        if Eliminator.elim(self):
            return True
        if Introducer.intro(self):
            return True

        branches = []

        p = self.copy()
        if Eliminator.NotE_force(p) and p.prove():
            branches.append(p.proof)

        p = self.copy()
        if Eliminator.ImpE_force(p) and p.prove():
            branches.append(p.proof)

        p = self.copy()
        if Eliminator.IffE_force(p) and p.prove():
            branches.append(p.proof)

        p = self.copy()
        if Eliminator.OrE(p):
            branches.append(p.proof)

        p = self.copy()
        if Introducer.IP(p):
            branches.append(p.proof)

        return self.proof.commit_best_branch(branches)

    def copy(self):
        return Prover(self.proof.copy(), self.seen)

    def _enter_state(self):
        proof = self.proof
        key = (frozenset(proof.assumptions()), proof.goal)

        cost = (proof.ip_count(), proof.line_count())
        formulas = frozenset(obj.formula for obj in proof.seq if obj.is_line())

        prev = self.seen.get(key)
        if prev is not None:
            prev_cost, prev_formulas = prev

            if cost >= prev_cost and formulas <= prev_formulas:
                return False

            if cost > prev_cost:
                cost = prev_cost
            if formulas < prev_formulas:
                formulas = prev_formulas

        self.seen[key] = (cost, formulas)
        return True


class Processor:

    @staticmethod
    def process(proof):
        Processor.remove_uncited(proof)
        return Processor.translate(proof)

    @staticmethod
    def remove_uncited(proof, citations=None):
        if citations is None:
            citations = proof.citations()

        while True:
            seq, n = [], len(proof.seq)

            for idx, obj in enumerate(proof.seq):
                if obj.id in citations or idx == n - 1:
                    if obj.is_subproof():
                        Processor.remove_uncited(obj, citations)
                    seq.append(obj)
                    continue

                if obj.is_line() and obj.rule in ("PR", "AS"):
                    seq.append(obj)

            proof.seq = seq
            if len(seq) == n:
                break
            citations = proof.citations()

    @staticmethod
    def translate(proof, start_idx=1, context=None, id_to_idx=None):
        if context is None:
            context = []
        if id_to_idx is None:
            id_to_idx = {}

        seq, idx = [], start_idx
        for obj in proof.seq:
            if obj.is_line():
                rule = Rules.rules.get(obj.rule) or getattr(Rules, obj.rule)
                citations = tuple(id_to_idx[c] for c in obj.citations)
                j = Justification(rule, citations)
                seq.append(Line(idx, obj.formula, j))
                id_to_idx[obj.id] = idx
                idx += 1
                continue

            subproof = Processor.translate(obj, idx, context + seq, id_to_idx)
            seq.append(subproof)
            new_idx = idx + obj.line_count()
            id_to_idx[obj.id] = (idx, new_idx - 1)
            idx = new_idx

        return Proof(seq, context)


def prove(premises, conclusion):
    if not is_valid(premises, conclusion):
        raise ProverError("Invalid argument, no proof exists.")
    seq = [_Line(p, "PR", ()) for p in premises]
    _proof = _Proof(seq, conclusion)
    p = Prover(_proof)

    if not p.prove():
        raise ProverError("Argument is valid, but no proof was found.")

    problem = Problem(TFL, premises, conclusion)
    proof = Processor.process(_proof)
    proof.seq = proof.seq[len(seq):]
    proof.context = problem.proof.context
    problem.proof = proof
    return problem
