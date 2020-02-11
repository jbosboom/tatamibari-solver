SVGTILER = svgtiler -p -j 16

all: variable wire terminate clause unsolved symbol

variable:
	ls variable-[01]*.txt | parallel -j 16 ./tatamibari-solver.py --output-pattern '{/.}.tsv' --solutions 1  {}
	ls variable-wide*.txt | parallel -j 16 ./tatamibari-solver.py --output-pattern '{/.}.tsv' --solutions 1 --reflex-three-corners {}
	$(SVGTILER) tatamibari.coffee variable-[01]*.tsv variable-wide-[01]*.tsv

wire:
	ls wire*txt | parallel -j 16 ./tatamibari-solver.py --output-pattern '{/.}.tsv' --solutions 1 --reflex-three-corners {}
	$(SVGTILER) tatamibari.coffee wire-[01]*.tsv

terminate:
	./tatamibari-solver.py --output-pattern 'terminate-0.tsv' --solutions 1 --reflex-three-corners --force 0,1,3,1 terminate-0.txt
	./tatamibari-solver.py --output-pattern 'terminate-1.tsv' --solutions 1 --reflex-three-corners --force 0,1,4,1 terminate-1.txt
	$(SVGTILER) tatamibari.coffee terminate-[01]*.tsv

clause:
	ls clause-[01][01]0.txt | parallel -j 16 ./tatamibari-solver.py --output-pattern '{/.}.tsv' --solutions 1 --reflex-three-corners --force 5,17,3,1 --force 17,2,1,1 {}
	ls clause-[01][01]1.txt | parallel -j 16 ./tatamibari-solver.py --output-pattern '{/.}.tsv' --solutions 1 --reflex-three-corners --force 6,17,3,1 --force 17,2,1,1 {}
	ls clause-000.txt | parallel -j 16 ./tatamibari-solver.py --output-pattern '{/.}.tsv' --solutions 1 --reflex-three-corners --covers subset --force 17,2,1,1 --force 19,6,2,2 --force 13,6,2,2 --force 19,12,2,2 --force 7,13,4,1 --force 19,18,2,2 --force 17,4,4,1 {}
	ls clause-001.txt | parallel -j 16 ./tatamibari-solver.py --output-pattern '{/.}.tsv' --solutions 1 --reflex-three-corners --force 6,17,3,1 --force 17,4,4,1 --force 17,2,1,1 {}
	ls clause-wide-[01][01]0.txt | parallel -j 16 ./tatamibari-solver.py --output-pattern '{/.}.tsv' --solutions 1 --reflex-three-corners --force 5,21,3,1 --force 17,2,1,1 {}
	ls clause-wide-101.txt | parallel -j 16 ./tatamibari-solver.py --output-pattern '{/.}.tsv' --solutions 1 --reflex-three-corners --force 6,21,3,1 --force 18,9,3,1 --force 17,17,4,1 --force 17,12,4,1 --force 18,20,3,1 --force 17,2,1,1 --force 14,4,4,1 {}
	$(SVGTILER) tatamibari.coffee clause-[01]*.tsv
	$(SVGTILER) clause-wide.coffee clause-wide-[01]*.tsv

unsolved:
	$(SVGTILER) tatamibari-unsolved.coffee *-unsolved.tsv

symbol:
	$(SVGTILER) tatamibari-unsolved.coffee symbol.xlsx
