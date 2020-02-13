# Tatamibari solver and NP-hardness gadgets

## Aviv Adler, Jeffrey Bosboom, Erik D. Demaine, Martin L. Demaine, Quanquan C. Liu, Jayson Lynch

This repository contains a Z3-based tool for solving Tatamibari puzzles and,
as an example set of puzzles, gadgets that prove the game NP-hard
(from a forthcoming paper by the same authors, "Tatamibari is NP-complete").

## Tatamibari solver

[`tatamibari-solver.py`](tatamibari-solver.py) solves Tatamibari puzzles
by reducing them to a satisfiability problem and solving them via
[Z3](https://github.com/Z3Prover/z3).

It has the following prerequisites:
* [Python 3.5+](https://www.python.org/)
* [Z3](https://github.com/Z3Prover/z3)
* [Python Z3 wrapper](https://pypi.org/project/z3-solver/)
  (`pip3 install z3-solver`)

## [NP-hardness gadgets](gadgets)

The NP-hardness gadgets are in the [`gadgets` directory](gadgets).
Within that directory, you can run `make` to solve the gadgets and
generate the figures of the paper.

In addition to the above prerequisites, you need the following software
to visualize the output:
* [svgtiler](https://github.com/edemaine/svgtiler)
