import unittest
from cnf_converter import parse_cfg, cfg_to_cnf, generate_words, is_cnf

class TestCNFConverter(unittest.TestCase):
    def test_parse_cfg_basic(self):
        cfg_str = "S -> AB | a\nA -> aA | ε\nB -> b"
        expected = {
            'S': [['A', 'B'], ['a']],
            'A': [['a', 'A'], ['ε']],
            'B': [['b']]
        }
        self.assertEqual(parse_cfg(cfg_str), expected)

    def test_parse_cfg_arrows_and_epsilon(self):
        cfg_str = "S → A\nA -> E"
        expected = {
            'S': [['A']],
            'A': [['ε']]
        }
        self.assertEqual(parse_cfg(cfg_str), expected)

    def test_cfg_to_cnf_produces_valid_cnf(self):
        cfg_str = "S -> AB | a\nA -> aA | ε\nB -> b"
        grammar = parse_cfg(cfg_str)
        cnf_str, steps = cfg_to_cnf(grammar)

        expected_titles = [
            'Original grammar',
            'After removing ε-productions',
            'After removing unit productions',
            'After removing useless symbols',
            'Chomsky Normal Form (CNF)'
        ]
        self.assertEqual([t for t, _ in steps], expected_titles)

        cnf = parse_cfg(cnf_str)
        self.assertTrue(is_cnf(cnf, 'S'))
        self.assertEqual(
            generate_words(grammar, 'S', max_length=3),
            generate_words(cnf, 'S', max_length=3)
        )

    def test_epsilon_only_from_start(self):
        cfg_str = "S -> A | ε\nA -> S B | a\nB -> b"
        grammar = parse_cfg(cfg_str)
        cnf_str, _ = cfg_to_cnf(grammar)
        cnf = parse_cfg(cnf_str)

        self.assertTrue(is_cnf(cnf, 'S0'))
        for nt, prods in cnf.items():
            for p in prods:
                if p == ['ε']:
                    self.assertEqual(nt, 'S0')

    def test_generate_words_simple(self):
        grammar = parse_cfg("S -> aS | b")
        words = generate_words(grammar, 'S', max_length=3)
        self.assertEqual(words, {'b', 'ab', 'aab'})

    def test_generate_words_with_epsilon(self):
        grammar = parse_cfg("S -> ε | a")
        words = generate_words(grammar, 'S', max_length=1)
        self.assertEqual(words, {'', 'a'})

    def test_epsilon_removal_correctness(self):
        cfg_str = "A -> B A B | B | ε\nB -> 0 0 | ε"
        grammar = parse_cfg(cfg_str)
        cnf_str, steps = cfg_to_cnf(grammar)

        epsilon_removed = None
        for title, g in steps:
            if title == 'After removing ε-productions':
                epsilon_removed = parse_cfg(g)
                break

        # no ε-productions should remain except possibly for the new start symbol
        for nt, prods in epsilon_removed.items():
            if nt == 'S0':
                continue
            self.assertNotIn(['ε'], prods)

        cnf = parse_cfg(cnf_str)
        for nt, prods in cnf.items():
            for p in prods:
                if p == ['ε']:
                    self.assertEqual(nt, 'S0')

if __name__ == '__main__':
    unittest.main()
