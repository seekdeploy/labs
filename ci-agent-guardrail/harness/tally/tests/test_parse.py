import unittest
from tally import parse_duration


class ParseDuration(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(parse_duration("45s"), 45)
        self.assertEqual(parse_duration("2m"), 120)

    def test_combined(self):
        self.assertEqual(parse_duration("1h30m"), 5400)
        self.assertEqual(parse_duration("1d2h"), 93600)

    def test_rejects_garbage(self):
        for bad in ["", "abc", "10x", "1h 30m", "h1"]:
            with self.assertRaises(ValueError):
                parse_duration(bad)


if __name__ == "__main__":
    unittest.main()
