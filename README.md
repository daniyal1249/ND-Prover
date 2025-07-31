# ND-Prover

An interactive Fitch-style natural deduction proof checker, implemented in Python.

Supports propositional, first-order, and modal logics (K, T, S4, S5) via a command-line interface.


## Logic Checklist

- [x] Propositional logic (TFL)
- [ ] First-order logic (FOL)
- [ ] Modal logic K (MLK)
- [ ] Modal logic T (MLT)
- [ ] Modal logic S4 (MLS4)
- [ ] Modal logic S5 (MLS5)


## Example Usage

```
$ python cli.py
Select logic (TFL, FOL, MLK, MLT, MLS4, MLS5): TFL
Enter premises (separated by "," or ";"): P -> Q, P
Enter conclusion: Q

 1 | P → Q      PR
 2 | P          PR
   |---

1 - Add a new line
2 - Begin a new subproof
3 - End the current subproof
4 - End the current subproof and begin a new one
5 - Delete the last line

Select action: 1
Enter line: Q ; ->E, 1,2

 1 | P → Q      PR
 2 | P          PR
   |---
 3 | Q          →E, 1,2

Proof complete! 🎉
```

A proof of the law of excluded middle (LEM) using ND-Prover: 

```
Proof of  ∴ P ∨ ¬P
------------------

 1 | | ¬(P ∨ ¬P)       AS
   | |-----------      
 2 | | | P             AS
   | | |---            
 3 | | | P ∨ ¬P        ∨I, 2
 4 | | | ⊥             ¬E, 1,3
 5 | | ¬P              ¬I, 2-4
 6 | | P ∨ ¬P          ∨I, 5
 7 | | ⊥               ¬E, 1,6
 8 | P ∨ ¬P            IP, 1-7

Proof complete! 🎉
```
