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
    import re
    arrow_pattern = re.compile(r'(->|→)')
    # Replace all arrows with a unique token, then split
    ARROW = '<<<ARROW>>>'
    text = arrow_pattern.sub(ARROW, cfg_str)
    # Now split into statements at each ARROW
    stmts = re.split(r'\n|(?<!^)' + ARROW, text)
    for stmt in stmts:
        if ARROW not in stmt:
            continue
        left, right = stmt.split(ARROW, 1)
        left = left.strip()
        productions = right.split('|')
        for prod in productions:
            prod = prod.strip()
            # Accept 'E' as epsilon (empty string)
            prod = prod.replace('E', 'ε')
            # If the production is space-separated, use split; otherwise, treat each char as a symbol
            if ' ' in prod:
                symbols = prod.split()
            else:
                symbols = list(prod) if prod != 'ε' else ['ε']
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
                if not new_prod:
                    if nt == start:
                        new_prod = ['ε']
                    else:
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
    # Step 1: Replace terminals in productions of length > 1 with new nonterminals
    new_grammar = defaultdict(list)
    term_map = {}
    term_counter = 1
    for nt, prods in grammar.items():
        for prod in prods:
            if len(prod) > 1:
                new_prod = []
                for symbol in prod:
                    # A terminal is a single lowercase letter or nonterminal is uppercase
                    if len(symbol) == 1 and symbol.islower():
                        if symbol not in term_map:
                            new_nt = f"T{term_counter}"
                            term_counter += 1
                            term_map[symbol] = new_nt
                        new_prod.append(term_map[symbol])
                    else:
                        new_prod.append(symbol)
                new_grammar[nt].append(new_prod)
            else:
                new_grammar[nt].append(prod)
    # Add productions for the new terminal nonterminals
    for t, nt_for_t in term_map.items():
        new_grammar[nt_for_t].append([t])

    # Step 2: Break up productions longer than 2
    final_grammar = defaultdict(list)
    var_counter = 1
    for nt, prods in new_grammar.items():
        for prod in prods:
            current = prod
            prev_nt = nt
            while len(current) > 2:
                new_nt = f"X{var_counter}"
                var_counter += 1
                final_grammar[prev_nt].append([current[0], new_nt])
                current = current[1:]
                prev_nt = new_nt
            final_grammar[prev_nt].append(current)
    # Remove any productions that are not strictly CNF (A -> BC or A -> a or S -> ε)
    cleaned_grammar = defaultdict(list)
    for nt, prods in final_grammar.items():
        for prod in prods:
            if len(prod) == 1:
                # Only allow ε for the start symbol
                if prod == ['ε']:
                    if nt == start:
                        cleaned_grammar[nt].append(prod)
                    # else: skip ε for non-start symbols
                else:
                    cleaned_grammar[nt].append(prod)
            elif len(prod) == 2 and all(s.isupper() for s in prod):
                cleaned_grammar[nt].append(prod)
    return dict(cleaned_grammar)

def format_grammar(grammar):
    lines = []
    for nt, prods in grammar.items():
        right = [" ".join(prod) for prod in prods]
        lines.append(f"{nt} -> {' | '.join(right)}")
    return "\n".join(lines)
