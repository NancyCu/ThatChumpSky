import unittest
from cnf_converter import parse_cfg, cfg_to_cnf, generate_words

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

    def test_cfg_to_cnf_steps_and_result(self):
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

        expected_cnf = parse_cfg("S -> a | b | A B\nA -> a | T1 A\nB -> b\nT1 -> a")

        def as_sets(g):
            return {nt: {tuple(p) for p in prods} for nt, prods in g.items()}

        self.assertEqual(as_sets(parse_cfg(cnf_str)), as_sets(expected_cnf))

    def test_generate_words_simple(self):
        grammar = parse_cfg("S -> aS | b")
        words = generate_words(grammar, 'S', max_length=3)
        self.assertEqual(words, {'b', 'ab', 'aab'})

    def test_generate_words_with_epsilon(self):
        grammar = parse_cfg("S -> ε | a")
        words = generate_words(grammar, 'S', max_length=1)
        self.assertEqual(words, {'', 'a'})

if __name__ == '__main__':
    unittest.main()
