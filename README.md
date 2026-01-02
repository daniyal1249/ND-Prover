# ND-Prover

A Fitch-style natural deduction proof generator and checker, implemented in Python.

Supports propositional, first-order, and modal logics (K, T, S4, S5).


![ND-Prover Demo](prover.gif)


## Installation

ND-Prover can be installed using pip:

    pip install nd-prover

or by directly cloning the git repository:

    git clone https://github.com/daniyal1249/nd-prover.git

and running the following in the cloned repo:

    pip install .


## Example Usage

```
$ nd-prover
Select logic (TFL, FOL, MLK, MLT, MLS4, MLS5, FOMLK, FOMLT, FOMLS4, FOMLS5): TFL
Enter premises (separated by "," or ";"), or "NA" if none: P -> Q, P
Enter conclusion: Q

 1 │ P → Q      PR
   │
 2 │ P          PR
   ├───

1 - Add a new line
2 - Begin a new subproof
3 - End the current subproof
4 - End the current subproof and begin a new one
5 - Delete the last line

Select edit: 1
Enter line: Q ; ->E, 1,2

 1 │ P → Q      PR
   │
 2 │ P          PR
   ├───
 3 │ Q          →E, 1,2

Proof complete! 🎉
```

A proof of the law of excluded middle (LEM) using ND-Prover: 

```
Proof of  ∴ P ∨ ¬P
──────────────────

 1 │ │ ¬(P ∨ ¬P)       AS
   │ ├───────────      
 2 │ │ │ P             AS
   │ │ ├───            
 3 │ │ │ P ∨ ¬P        ∨I, 2
   │ │ │               
 4 │ │ │ ⊥             ¬E, 1,3
   │ │                 
 5 │ │ ¬P              ¬I, 2-4
   │ │                 
 6 │ │ P ∨ ¬P          ∨I, 5
   │ │                 
 7 │ │ ⊥               ¬E, 1,6
   │                   
 8 │ P ∨ ¬P            IP, 1-7

Proof complete! 🎉
```

A proof that identity is symmetric: 

```
Proof of  ∴ ∀x∀y(x = y → y = x)
───────────────────────────────

 1 │ │ a = b                  AS
   │ ├───────                 
 2 │ │ a = a                  =I
   │ │                        
 3 │ │ b = a                  =E, 1,2
   │                          
 4 │ a = b → b = a            →I, 1-3
   │                          
 5 │ ∀y(a = y → y = a)        ∀I, 4
   │                          
 6 │ ∀x∀y(x = y → y = x)      ∀I, 5

Proof complete! 🎉
```

A proof in modal logic S5: 

```
Proof of ♢□A ∴ □A
─────────────────

 1 │ ♢□A          PR
   ├─────         
 2 │ ¬□¬□A        Def♢, 1
   │              
 3 │ │ ¬□A        AS
   │ ├─────       
 4 │ │ │ □        AS
   │ │ ├───       
 5 │ │ │ ¬□A      R5, 3
   │ │            
 6 │ │ □¬□A       □I, 4-5
   │ │            
 7 │ │ ⊥          ¬E, 2,6
   │              
 8 │ □A           IP, 3-7

Proof complete! 🎉
```
