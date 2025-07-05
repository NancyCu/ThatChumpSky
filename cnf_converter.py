"""Utilities to convert a context free grammar to strict Chomsky Normal Form."""

from __future__ import annotations

import re
from collections import defaultdict


########################
# Parsing and printing #
########################

def parse_cfg(text: str) -> dict[str, list[list[str]]]:
    """Parse a grammar from ``text``.

    Each line must have the form ``A -> B C | a``. ``E`` is treated as ``ε``.
    Terminals can be written without spaces, e.g. ``AB`` means ``A B`` when both
    symbols are non-terminals.  The function returns ``{lhs: [[rhs], ...]}``.
    """

    grammar: dict[str, list[list[str]]] = defaultdict(list)
    arrow = re.compile(r"\s*(->|→)\s*")
    for line in text.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        m = arrow.split(line, maxsplit=1)
        if len(m) < 3:
            continue
        lhs, rhs = m[0].strip(), m[2].strip()
        for alt in rhs.split("|"):
            alt = alt.strip().replace("E", "ε")
            if alt == "ε":
                grammar[lhs].append(["ε"])
            else:
                if " " in alt:
                    symbols = alt.split()
                else:
                    symbols = list(alt)
                grammar[lhs].append(symbols)
    return dict(grammar)


def format_grammar(grammar: dict[str, list[list[str]]], start: str) -> str:
    """Return a nicely formatted grammar sorted as required."""

    lines = []
    order = [start] + sorted(nt for nt in grammar if nt != start)
    for nt in order:
        prods = grammar.get(nt, [])
        unique: list[list[str]] = []
        for p in prods:
            if p not in unique:
                unique.append(p)
        rhs = [" ".join(p) for p in unique]
        if rhs:
            lines.append(f"{nt} → {' | '.join(rhs)}")
    return "\n".join(lines)


#############################
# CNF transformation steps   #
#############################

def cfg_to_cnf(grammar: dict[str, list[list[str]]]) -> tuple[str, list[tuple[str, str]]]:
    """Convert ``grammar`` to strict CNF.

    Returns ``(cnf_string, steps)`` where ``steps`` is a list of
    ``(title, formatted_grammar)`` pairs describing each transformation stage.
    """

    steps: list[tuple[str, str]] = []

    def add_step(title: str, g: dict[str, list[list[str]]]):
        steps.append((title, format_grammar(g, start_symbol)))

    # 1. create new start symbol
    original_start = next(iter(grammar))
    start_symbol = "S0"
    idx = 0
    while start_symbol in grammar:
        idx += 1
        start_symbol = f"S{idx}"
    grammar = {start_symbol: [[original_start]], **grammar}
    add_step("Add a new start symbol", grammar)

    # 2. remove epsilon-productions
    grammar = remove_epsilons(grammar, start_symbol)
    add_step("Remove ε-productions", grammar)

    # 3. remove unit productions
    grammar = remove_units(grammar)
    add_step("Remove unit productions", grammar)

    # 4. remove useless symbols
    grammar = remove_useless(grammar, start_symbol)
    add_step("Remove useless symbols", grammar)

    # 5. replace terminals in long rules
    grammar = replace_terminals(grammar)
    add_step("Replace terminals in long rules", grammar)

    # 6. binarize productions
    grammar = binarize(grammar)
    add_step("Binarize long rules", grammar)

    # final formatted grammar
    cnf = format_grammar(grammar, start_symbol)
    steps.append(("Chomsky Normal Form", cnf))
    return cnf, steps


def remove_epsilons(grammar: dict[str, list[list[str]]], start: str) -> dict[str, list[list[str]]]:
    """Eliminate ε-productions."""

    nullable: set[str] = set()

    changed = True
    while changed:
        changed = False
        for nt, prods in grammar.items():
            if nt in nullable:
                continue
            for prod in prods:
                if prod == ["ε"] or all(sym in nullable for sym in prod):
                    nullable.add(nt)
                    changed = True
                    break

    new_grammar: dict[str, list[list[str]]] = defaultdict(list)
    for nt, prods in grammar.items():
        for prod in prods:
            if prod == ["ε"]:
                continue
            positions = [i for i, sym in enumerate(prod) if sym in nullable]
            subsets = 1 << len(positions)
            for mask in range(subsets):
                new_prod: list[str] = []
                for i, sym in enumerate(prod):
                    if i in positions and (mask >> positions.index(i)) & 1:
                        continue
                    new_prod.append(sym)
                if not new_prod:
                    if nt == start:
                        new_prod = ["ε"]
                    else:
                        continue
                if new_prod not in new_grammar[nt]:
                    new_grammar[nt].append(new_prod)
    return dict(new_grammar)


def remove_units(grammar: dict[str, list[list[str]]]) -> dict[str, list[list[str]]]:
    """Eliminate unit productions."""

    new_grammar: dict[str, list[list[str]]] = defaultdict(list)
    for nt in grammar:
        queue = [nt]
        visited: set[str] = set()
        while queue:
            current = queue.pop(0)
            for prod in grammar.get(current, []):
                if len(prod) == 1 and prod[0] in grammar:
                    if prod[0] not in visited:
                        visited.add(prod[0])
                        queue.append(prod[0])
                else:
                    if prod not in new_grammar[nt]:
                        new_grammar[nt].append(prod)
    return dict(new_grammar)


def remove_useless(grammar: dict[str, list[list[str]]], start: str) -> dict[str, list[list[str]]]:
    """Remove non-generating and unreachable symbols."""

    generating: set[str] = set()
    changed = True
    while changed:
        changed = False
        for nt, prods in grammar.items():
            if nt in generating:
                continue
            for prod in prods:
                if all(sym not in grammar or sym in generating for sym in prod if sym != "ε"):
                    generating.add(nt)
                    changed = True
                    break

    grammar = {
        nt: [p for p in prods if all(sym not in grammar or sym in generating for sym in p if sym != "ε")]
        for nt, prods in grammar.items()
        if nt in generating
    }

    reachable: set[str] = set()
    queue = [start]
    while queue:
        nt = queue.pop(0)
        if nt not in reachable:
            reachable.add(nt)
            for prod in grammar.get(nt, []):
                for sym in prod:
                    if sym in grammar and sym not in reachable:
                        queue.append(sym)

    grammar = {nt: prods for nt, prods in grammar.items() if nt in reachable}
    return grammar


def replace_terminals(grammar: dict[str, list[list[str]]]) -> dict[str, list[list[str]]]:
    """Introduce variables for terminals appearing in long productions."""

    counter = 1
    mapping: dict[str, str] = {}
    new_grammar: dict[str, list[list[str]]] = defaultdict(list)

    for nt, prods in grammar.items():
        for prod in prods:
            if len(prod) > 1:
                new_prod: list[str] = []
                for sym in prod:
                    if sym in grammar:
                        new_prod.append(sym)
                    elif sym == "ε":
                        new_prod.append(sym)
                    else:  # terminal
                        if sym not in mapping:
                            name = f"T_{sym}"
                            while name in grammar or name in mapping.values():
                                counter += 1
                                name = f"T_{sym}{counter}"
                            mapping[sym] = name
                        new_prod.append(mapping[sym])
                new_grammar[nt].append(new_prod)
            else:
                new_grammar[nt].append(prod)

    for term, var in mapping.items():
        new_grammar[var].append([term])

    return dict(new_grammar)


def binarize(grammar: dict[str, list[list[str]]]) -> dict[str, list[list[str]]]:
    """Binarize productions longer than 2."""

    counter = 1

    def fresh() -> str:
        nonlocal counter
        name = f"X{counter}"
        counter += 1
        while name in grammar:
            name = f"X{counter}"
            counter += 1
        return name

    new_grammar: dict[str, list[list[str]]] = defaultdict(list)

    for nt, prods in grammar.items():
        for prod in prods:
            if len(prod) <= 2:
                new_grammar[nt].append(prod)
                continue

            symbols = prod
            prev = nt
            while len(symbols) > 2:
                y = fresh()
                new_grammar[prev].append([symbols[0], y])
                symbols = symbols[1:]
                prev = y
            new_grammar[prev].append(symbols)

    return dict(new_grammar)


if __name__ == "__main__":  # simple manual test
    example = """S -> ASA | aB\nA -> BIS\nB -> b | ε"""
    g = parse_cfg(example)
    cnf, steps = cfg_to_cnf(g)
    for title, text in steps:
        print("---", title)
        print(text)
    print("\nCNF:\n", cnf)

