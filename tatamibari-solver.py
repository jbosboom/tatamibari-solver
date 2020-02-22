#!/usr/bin/python3
import itertools
import os
import sys, collections, z3, re, argparse
from enum import Enum
from operator import itemgetter
from typing import List, Set, Dict, Iterator

Point = collections.namedtuple('Point', ['r', 'c'])
Rect = collections.namedtuple('Rect', ['r', 'c', 'h', 'w'])

def str_to_rect(s, error=''):
    m = re.fullmatch('(\d+),(\d+),(\d+),(\d+)', s)
    if not m:
        raise AssertionError('str_to_rect:'+s+' '+error)
    return Rect(int(m[1]), int(m[2]), int(m[3]), int(m[4]))

class Clue(Enum):
    PLUS = '+'
    VERT = '|'
    HORIZ = '-'

class Puzzle(object):
    def __init__(self, cells, clues):
        self.cells: Set[Point] = frozenset(cells)
        self.clues: Dict[Point, Clue] = clues # Python doesn't have frozendict
        self.rmax: int = max(map(itemgetter(0), self.cells)) + 1
        self.cmax: int = max(map(itemgetter(1), self.cells)) + 1

def parse(stream) -> Puzzle:
    cells: Set[Point] = set()
    clues: Dict[Point, Clue] = {}
    for row, line in enumerate(stream):
        line = line.rstrip()
        for col, char in enumerate(line):
            if char == ' ': continue # for nonrectangular grids (use '_' for empty cells)
            p = Point(row, col)
            cells.add(p)
            try:
                clues[p] = Clue(char)
            except ValueError:
                pass # not a clue
    return Puzzle(cells, clues)

def solve(puzzle: Puzzle, forced_rects: Set[Rect] = frozenset(),
        clue_constraints: str = 'hard',
        cover_constraints: str = 'exact',
        corner_constraints: str = 'hard',
        reflex_three_corners: bool = False) -> Iterator[List[Rect]]:
    rect_to_var: Dict[Rect, z3.Bool] = {}
    # Each cell is covered by exactly one rect.
    cell_to_rects: Dict[Point, z3.Bool] = {c: list() for c in puzzle.cells}
    # Each clue is satisfied by exactly one rect (of the right shape).
    clue_to_rects: Dict[Point, z3.Bool] = {c: list() for c in puzzle.clues.keys()}
    # Maps cells to rects having a there, for tracking four-corner violations.
    # The values may be empty (but most won't be).
    ul_to_rects: Dict[Point, z3.Bool] = {c: list() for c in puzzle.cells}
    ur_to_rects: Dict[Point, z3.Bool] = {c: list() for c in puzzle.cells}
    ll_to_rects: Dict[Point, z3.Bool] = {c: list() for c in puzzle.cells}
    lr_to_rects: Dict[Point, z3.Bool] = {c: list() for c in puzzle.cells}
    for r1 in range(puzzle.rmax):
        for c1 in range(puzzle.cmax):
            for r2 in range(r1, puzzle.rmax):
                for c2 in range(c1, puzzle.cmax):
                    width, height = c2 - c1 + 1, r2 - r1 + 1  # inclusive
                    rect = Rect(r1, c1, height, width)
                    rect_cells = {Point(r, c) for r in range(r1, r2+1) for c in range(c1, c2+1)}
                    # Depending on where the violation was, we may be able to
                    # break the r2 loop early for both of these checks.
                    if not rect_cells <= puzzle.cells:
                        if rect in forced_rects:
                            raise RuntimeError('forced rect {} contains holes {}'.format(rect, rect_cells - puzzle.cells))
                        break
                    rect_clues = rect_cells & puzzle.clues.keys()
                    if len(rect_clues) > 1:
                        if rect in forced_rects:
                            raise RuntimeError('forced rect {} contains multiple clues at {}'.format(rect, rect_clues))
                        break
                    if len(rect_clues) == 0:
                        if rect in forced_rects:
                            raise RuntimeError('forced rect {} contains no clues'.format(rect))
                        continue # expanding the rect may add a clue
                    clue_cell = rect_clues.pop()
                    clue = puzzle.clues[clue_cell]
                    expected_clue = Clue.PLUS if width == height else Clue.VERT if width < height else Clue.HORIZ
                    if clue != expected_clue and clue_constraints == 'hard':
                        if rect in forced_rects:
                            raise RuntimeError('forced rect {} contains a {}, but is shaped for a {}'.format(rect, clue, expected_clue))
                        continue

                    var = z3.Bool('{},{},{},{}'.format(r1, c1, height, width))
                    rect_to_var[rect] = var
                    for c in rect_cells:
                        cell_to_rects[c].append(var)
                    clue_to_rects[clue_cell].append(var)
                    ul_to_rects[Point(r1, c1)].append(var)
                    ur_to_rects[Point(r1, c2)].append(var)
                    ll_to_rects[Point(r2, c1)].append(var)
                    lr_to_rects[Point(r2, c2)].append(var)

    missing_forced_rects = forced_rects - rect_to_var.keys()
    if missing_forced_rects:
        # We could add a command-line flag to disable pruning to get a
        # better error message here.
        raise RuntimeError('forced rects {} were pruned'.format(missing_forced_rects))

    for cell, rects in cell_to_rects.items():
        if not rects:
            print('cell', cell, 'has no covering rects')
    for clue_cell, rects in clue_to_rects.items():
        if not rects:
            print('clue', puzzle.clues[clue_cell], 'in', clue_cell, 'has no candidate rects')

    solver = z3.Optimize()
    for c in puzzle.cells:
        if c in clue_to_rects and clue_constraints == 'hard':
            solver.add(z3.PbEq([(r, 1) for r in clue_to_rects[c]], 1))
        elif cover_constraints == 'exact':
            solver.add(z3.PbEq([(r, 1) for r in cell_to_rects[c]], 1))
        elif cover_constraints == 'subset':
            solver.add(z3.PbLe([(r, 1) for r in cell_to_rects[c]], 1))
            solver.add_soft(z3.PbGe([(r, 1) for r in cell_to_rects[c]], 1), 1, 'cover')
        elif cover_constraints == 'superset':
            solver.add_soft(z3.PbLe([(r, 1) for r in cell_to_rects[c]], 1), 1, 'cover')
            solver.add(z3.PbGe([(r, 1) for r in cell_to_rects[c]], 1))
        elif cover_constraints == 'incomparable':
            solver.add_soft(z3.PbEq([(r, 1) for r in cell_to_rects[c]], 1), 1, 'cover')
        else:
            raise AssertionError('bad cover_constraints: ' + cover_constraints)
    if corner_constraints != 'ignore': # skip the loop if we wouldn't add anyway
        for c in puzzle.cells:
            for r1 in lr_to_rects.get(c, []):
                for r2 in ll_to_rects.get(Point(c.r, c.c+1), []):
                    for r3 in ur_to_rects.get(Point(c.r+1, c.c), []):
                        for r4 in ul_to_rects.get(Point(c.r+1, c.c+1), []):
                            if corner_constraints == 'hard':
                                solver.add(z3.PbLe([(r1, 1), (r2, 1), (r3, 1), (r4, 1)], 3))
                            elif corner_constraints == 'soft':
                                solver.add_soft(z3.PbLe([(r1, 1), (r2, 1), (r3, 1), (r4, 1)], 3), 1, 'corner')
                            else:
                                raise AssertionError('bad corner_constraints: '+corner_constraints)
        if reflex_three_corners:
            holes = [Point(r, c) for r in range(puzzle.rmax) for c in range(puzzle.cmax) if Point(r, c) not in puzzle.cells]
            for c in holes:
                for r2 in ll_to_rects.get(Point(c.r, c.c+1), []):
                    for r3 in ur_to_rects.get(Point(c.r+1, c.c), []):
                        for r4 in ul_to_rects.get(Point(c.r+1, c.c+1), []):
                            if corner_constraints == 'hard':
                                solver.add(z3.PbLe([(r2, 1), (r3, 1), (r4, 1)], 2))
                            elif corner_constraints == 'soft':
                                solver.add_soft(z3.PbLe([(r2, 1), (r3, 1), (r4, 1)], 2), 1, 'corner')
                            else:
                                raise AssertionError('bad corner_constraints: ' + corner_constraints)
                for r2 in lr_to_rects.get(Point(c.r, c.c-1), []):
                    for r3 in ur_to_rects.get(Point(c.r+1, c.c-1), []):
                        for r4 in ul_to_rects.get(Point(c.r+1, c.c), []):
                            if corner_constraints == 'hard':
                                solver.add(z3.PbLe([(r2, 1), (r3, 1), (r4, 1)], 2))
                            elif corner_constraints == 'soft':
                                solver.add_soft(z3.PbLe([(r2, 1), (r3, 1), (r4, 1)], 2), 1, 'corner')
                            else:
                                raise AssertionError('bad corner_constraints: ' + corner_constraints)
                for r2 in lr_to_rects.get(Point(c.r-1, c.c), []):
                    for r3 in ll_to_rects.get(Point(c.r-1, c.c+1), []):
                        for r4 in ul_to_rects.get(Point(c.r, c.c+1), []):
                            if corner_constraints == 'hard':
                                solver.add(z3.PbLe([(r2, 1), (r3, 1), (r4, 1)], 2))
                            elif corner_constraints == 'soft':
                                solver.add_soft(z3.PbLe([(r2, 1), (r3, 1), (r4, 1)], 2), 1, 'corner')
                            else:
                                raise AssertionError('bad corner_constraints: ' + corner_constraints)
                for r2 in lr_to_rects.get(Point(c.r-1, c.c-1), []):
                    for r3 in ll_to_rects.get(Point(c.r-1, c.c), []):
                        for r4 in ur_to_rects.get(Point(c.r, c.c-1), []):
                            if corner_constraints == 'hard':
                                solver.add(z3.PbLe([(r2, 1), (r3, 1), (r4, 1)], 2))
                            elif corner_constraints == 'soft':
                                solver.add_soft(z3.PbLe([(r2, 1), (r3, 1), (r4, 1)], 2), 1, 'corner')
                            else:
                                raise AssertionError('bad corner_constraints: ' + corner_constraints)
    if forced_rects:
        solver.add(z3.And(list(rect_to_var[r] for r in forced_rects)))

    while solver.check() == z3.sat:
        model = solver.model()
        soln: List[Rect] = []
        blockers = []
        for d in model.decls():
            if z3.is_true(model[d]):
                soln.append(str_to_rect(d.name()))
            # Build a constraint that prevents this model from being returned again.
            # https://stackoverflow.com/a/11869410/3614835
            blockers.append(d() != model[d])
        soln.sort()
        yield soln
        solver.add(z3.Or(blockers))

def format_soln(puzzle: Puzzle, soln: List[Rect]) -> str:
    data = [[' ' if Point(r,c) in puzzle.cells else '' for c in range(puzzle.cmax)] for r in range(puzzle.rmax)]
    for i, rect in enumerate(soln):
        for r in range(rect.r, rect.r+rect.h):
            data[r][rect.c:rect.c+rect.w] = [str(i)] * rect.w
    for cell, clue in puzzle.clues.items():
        data[cell.r][cell.c] += clue.value
    return '\n'.join(map('\t'.join, data))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--solutions", type=int, default=2, help='max number of solutions to search for (default 2, to check uniqueness')
    # Can't use 'append' with sets (grumble nongenericity).
    parser.add_argument("--force", type=str_to_rect, default=[], action='append', help='r,c,h,w specification of a rect to be forced in all solutions (may be passed multiple times)')
    parser.add_argument("--output-pattern", "--output-template", type=str, help='output filename pattern (use {} for index substitution)')
    # we might add a soft constraint here later
    parser.add_argument("--clues", type=str, choices=('hard', 'ignore'), default='hard', help="interpretation of clue constraints on the shape of their containing rect")
    parser.add_argument("--covers", type=str, choices=('exact', 'subset', 'superset', 'incomparable', 'ignore'), default='exact', help='interpretation of covering clues')
    parser.add_argument("--corners", type=str, choices=('hard', 'soft', 'ignore'), default='hard', help="interpretation of four-corner constraints")
    parser.add_argument("--reflex-three-corners", "--reflex-corners", action='store_true', default=False, help="impose three-corner constraint at reflex corners near holes")
    parser.add_argument("puzzlefile", type=argparse.FileType('r'))
    args = parser.parse_args()

    if args.output_pattern:
        # Because it would suck to wait for the solver only to find each output overwrote the last.
        if args.solutions > 1 and '{}' not in args.output_pattern:
            print('specified output pattern "{}" contains no substitution, but multiple solutions ({}) possible'.format(args.output_pattern, args.solutions))
        # Because it would suck to wait for the solver only to get a permission error.
        first_file = args.output_pattern.format(0)
        open(first_file, 'w').close()
        os.remove(first_file)

    if args.clues == 'hard' and args.covers in ('superset', 'incomparable'):
        print('warning: because clue constraints are hard, clues cannot be multiply-covered')

    puzzle = parse(args.puzzlefile)
    soln_gen = solve(puzzle, forced_rects=set(args.force), clue_constraints=args.clues,
            cover_constraints=args.covers, corner_constraints=args.corners,
            reflex_three_corners=args.reflex_three_corners)
    i = -1 # ensure i is defined even when there are no solutions
    for i, soln in enumerate(itertools.islice(soln_gen, args.solutions)):
        if args.output_pattern:
            with open(args.output_pattern.format(i), 'w') as f:
                f.write(format_soln(puzzle, soln))
        else:
            if i: print()
            print(format_soln(puzzle, soln))
    print('{}: found {} solutions ({} requested{})'.format(
            args.puzzlefile.name, i+1, args.solutions,
            ', so there may be more' if i+1 == args.solutions else
            ", so that's all of them" if i+1 > 0 else ""))
