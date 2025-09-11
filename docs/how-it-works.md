# How it works


## Solver Process
The solver solves in three main stages: Task Interpretation, Program Generation, Program Abstraction, and Rule Learning

### 1. Task Interpretation Step

* Load task file into ARCKG
* Generate complete comparison receipts with the ARCKG

### 2. Program Generation Step
Task is conquerred one pair at a time.

The search level of comparison is deepened in a top-down manner. (PAIR -> GRID -> OBJECT -> PIXEL)

1) Traverse through rule files in rule_basket and find applicable rules of the current search level.
2) Stack transformation DSLs in applicable rules to make `def solve()`.
3) Check if applying the current `def solve()` to the input grid results to the output grid.
    * If it matches, pause program generation step and move to the next pair.
    * If it doesnt, proceed program generation step.
4) Proceed to deeper comparison and do the repeat 1-3.


### 3. Program Abstraction Step

By the end of Program Generation Step, we will have at least one program for each pair.

The programs are compared to find the generalized version of themselves.

* TBW


### 4. Rule Learning

* TBW
