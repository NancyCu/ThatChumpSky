# cnf_converter.py
"""
Module to parse a context-free grammar and convert it to Chomsky Normal Form (CNF).
"""
import re
from collections import defaultdict

def parse_cfg(cfg_str):
    """
    Parse a CFG from a string. Returns a dictionary: {nonterminal: [[symbols], ...], ...}
    """
    grammar = defaultdict(list)
    # Accept both '->' and '→' as arrows, and allow multiple productions per line
    arrow_pattern = re.compile(r'\s*(->|→)\s*')
    for line in cfg_str.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        # Split into left and right at the first arrow
        m = arrow_pattern.split(line, maxsplit=1)
        if len(m) < 3:
            continue  # skip invalid lines
        left = m[0].strip()
        right = m[2].strip()
        # Split right side by '|'
        productions = [p.strip() for p in right.split('|')]
        for prod in productions:
            # Accept 'E' or 'ε' as epsilon (empty string)
            prod = prod.replace('E', 'ε')
            if prod == 'ε':
                symbols = ['ε']
            else:
                # Split by whitespace, or treat as single symbols if no spaces
                if ' ' in prod:
                    symbols = prod.split()
                else:
                    symbols = list(prod)
            grammar[left].append(symbols)
    return dict(grammar)

def cfg_to_cnf(grammar):
    """
    Convert a CFG (as a dict) to Chomsky Normal Form. Returns a string representation and step-by-step transformations.
    """
    steps = []
    def add_step(title, g):
        steps.append((title, format_grammar(g)))

    # Step 0: Add new start symbol if start symbol appears on RHS
    start = next(iter(grammar))
    new_start = "S0"
    if any(start in prod for prods in grammar.values() for prod in prods):
        grammar = {**{new_start: [[start]]}, **grammar}
        start = new_start
        add_step("Add new start symbol", grammar)
    else:
        add_step("Original grammar", grammar)

    # Step 1: Remove null (epsilon) productions
    grammar = remove_null_productions(grammar, start)
    # Defensive sweep to ensure no stray ε remain
    for A in list(grammar):
        if A != start and ['ε'] in grammar[A]:
            grammar[A] = [p for p in grammar[A] if p != ['ε']]
    add_step("After removing ε-productions", grammar)

    # Step 2: Remove unit productions
    grammar = remove_unit_productions(grammar)
    add_step("After removing unit productions", grammar)

    # Step 3: Remove useless symbols
    grammar = remove_useless_symbols(grammar, start)
    add_step("After removing useless symbols", grammar)

    # Step 4: Convert to CNF
    grammar = convert_to_cnf(grammar, start)
    add_step("Chomsky Normal Form (CNF)", grammar)

    return format_grammar(grammar), steps

def generate_words(grammar, start=None, max_length=4, max_words=20):
    """Generate words from the grammar up to a given length.

    Parameters
    ----------
    grammar : dict
        The CFG as produced by ``parse_cfg``.
    start : str, optional
        Start symbol. If ``None`` the first key of ``grammar`` is used.
    max_length : int, default 4
        Maximum length of words (in terminal symbols).
    max_words : int, default 20
        Maximum number of words to generate.

    Returns
    -------
    list of str
        Sorted list of generated words.
    """
    if start is None:
        start = next(iter(grammar))

    words = set()
    from collections import deque

    queue = deque([[start]])

    while queue and len(words) < max_words:
        seq = queue.popleft()

        # Current length ignoring nonterminals and epsilons
        current_word = "".join(s for s in seq if s not in grammar and s != "ε")
        if len(current_word) > max_length:
            continue

        # If sequence contains only terminals
        if all(s not in grammar for s in seq):
            words.add(current_word)
            continue

        # Expand the first nonterminal in the sequence
        for i, sym in enumerate(seq):
            if sym in grammar:
                for prod in grammar[sym]:
                    # Skip epsilon in the middle of sequences
                    new_seq = seq[:i] + [t for t in prod if t != "ε"] + seq[i+1:]
                    queue.append(new_seq)
                break

    return {w for w in words if len(w) <= max_length}

def remove_null_productions(grammar, start):
    # Find nullable nonterminals
    nullable = set()
    for nt, prods in grammar.items():
        for prod in prods:
            if prod == ['ε']:
                nullable.add(nt)
    changed = True
    while changed:
        changed = False
        for nt, prods in grammar.items():
            for prod in prods:
                if all(symbol in nullable for symbol in prod):
                    if nt not in nullable:
                        nullable.add(nt)
                        changed = True
    # Remove epsilon productions and add all possible combinations for nullable
    new_grammar = defaultdict(list)
    for nt, prods in grammar.items():
        for prod in prods:
            if prod == ['ε']:
                continue
            # Generate all combinations by including/excluding nullable symbols
            positions = [i for i, s in enumerate(prod) if s in nullable]
            total = 1 << len(positions)
            for mask in range(total):
                new_prod = []
                for i, symbol in enumerate(prod):
                    if i in positions:
                        # If the bit is set, skip this symbol (remove it)
                        if (mask >> positions.index(i)) & 1:
                            continue
                    new_prod.append(symbol)
                # keep ε only for the start symbol
                if not new_prod:
                    if nt == start and ['ε'] not in new_grammar[nt]:
                        new_grammar[nt].append(['ε'])
                    continue
                if new_prod not in new_grammar[nt]:
                    new_grammar[nt].append(new_prod)
    return dict(new_grammar)

def remove_unit_productions(grammar):
    new_grammar = defaultdict(list)
    for nt in grammar:
        # BFS to find all non-unit productions reachable from nt
        queue = [nt]
        visited = set()
        while queue:
            current = queue.pop(0)
            for prod in grammar.get(current, []):
                if len(prod) == 1 and prod[0] in grammar:
                    if prod[0] not in visited:
                        queue.append(prod[0])
                        visited.add(prod[0])
                else:
                    if prod not in new_grammar[nt]:
                        new_grammar[nt].append(prod)
    return dict(new_grammar)

def remove_useless_symbols(grammar, start):
    # Step 1: Remove non-generating symbols
    generating = set()
    for nt, prods in grammar.items():
        for prod in prods:
            if all(s not in grammar for s in prod):
                generating.add(nt)
    changed = True
    while changed:
        changed = False
        for nt, prods in grammar.items():
            for prod in prods:
                if all(s in generating or s not in grammar for s in prod):
                    if nt not in generating:
                        generating.add(nt)
                        changed = True
    grammar = {nt: [prod for prod in prods if all(s in generating or s not in grammar for s in prod)]
               for nt, prods in grammar.items() if nt in generating}
    # Step 2: Remove unreachable symbols
    reachable = set()
    queue = [start]
    while queue:
        nt = queue.pop(0)
        if nt not in reachable:
            reachable.add(nt)
            for prod in grammar.get(nt, []):
                for s in prod:
                    if s in grammar and s not in reachable:
                        queue.append(s)
    grammar = {nt: prods for nt, prods in grammar.items() if nt in reachable}
    return grammar

def convert_to_cnf(grammar, start):
    """Transform ``grammar`` into Chomsky Normal Form."""

    # ------------------------------------------------------------------
    # Step 1: Replace terminals in productions of length > 1 with new
    # nonterminals.  Terminals are any symbols that never appear on the
    # left-hand side of a rule.
    # ------------------------------------------------------------------
    new_grammar = defaultdict(list)
    term_map = {}
    term_id = 1

    def get_term_var(t):
        nonlocal term_id
        if t not in term_map:
            # Use deterministic numbering so tests can rely on names
            term_map[t] = f"T{term_id}"
            term_id += 1
        return term_map[t]

    for nt, prods in grammar.items():
        for prod in prods:
            if len(prod) > 1:
                replaced = []
                for sym in prod:
                    if sym in grammar or sym == "ε":
                        replaced.append(sym)
                    else:
                        replaced.append(get_term_var(sym))
                new_grammar[nt].append(replaced)
            else:
                new_grammar[nt].append(prod)

    for t, var in term_map.items():
        new_grammar[var].append([t])

    # ------------------------------------------------------------------
    # Step 2: Break up productions longer than 2 symbols by introducing new
    # variables.  Productions are decomposed from the left so that A -> B C D
    # becomes A -> B X1, X1 -> C D.
    # ------------------------------------------------------------------
    final_grammar = defaultdict(list)
    chain_id = 1
    for nt, prods in new_grammar.items():
        for prod in prods:
            if len(prod) <= 2:
                final_grammar[nt].append(prod)
                continue

            current = prod
            prev = nt
            while len(current) > 2:
                first, second = current[0], current[1]
                new_var = f"X{chain_id}"
                chain_id += 1
                final_grammar[prev].append([first, new_var])
                prev = new_var
                current = current[1:]
            final_grammar[prev].append(current)

    # ------------------------------------------------------------------
    # Step 3: Validate and keep only productions allowed by CNF.  The only
    # permitted forms are::
    #   A -> a
    #   A -> B C
    # with ``ε`` allowed only for the start symbol.
    # ------------------------------------------------------------------
    cleaned = defaultdict(list)
    nonterminals = set(final_grammar.keys())
    for prods in final_grammar.values():
        for prod in prods:
            for sym in prod:
                if sym in final_grammar:
                    nonterminals.add(sym)

    for nt, prods in final_grammar.items():
        for prod in prods:
            if prod == ["ε"]:
                if nt == start:
                    if prod not in cleaned[nt]:
                        cleaned[nt].append(prod)
                continue

            if len(prod) == 1:
                if prod[0] not in nonterminals:
                    if prod not in cleaned[nt]:
                        cleaned[nt].append(prod)
            elif len(prod) == 2:
                if all(sym in nonterminals for sym in prod):
                    if prod not in cleaned[nt]:
                        cleaned[nt].append(prod)

    return dict(cleaned)

def format_grammar(grammar):
    lines = []
    for nt, prods in grammar.items():
        right = [" ".join(prod) for prod in prods]
        lines.append(f"{nt} -> {' | '.join(right)}")
    return "\n".join(lines)


def is_cnf(grammar, start):
    """Return ``True`` if ``grammar`` is in Chomsky Normal Form."""
    for nt, prods in grammar.items():
        for prod in prods:
            if prod == ["ε"]:
                if nt != start:
                    return False
            elif len(prod) == 1:
                if prod[0] in grammar:
                    return False
            elif len(prod) == 2:
                if not all(sym in grammar for sym in prod):
                    return False
            else:
                return False
    return True

