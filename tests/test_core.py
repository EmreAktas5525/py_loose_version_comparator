import unittest

from py_loose_version_comparator import (
    LooseVersion,
    compare_versions,
    parse_version,
    sort_versions,
)


class ParseVersionTests(unittest.TestCase):
    def test_splits_on_digit_non_digit_boundaries(self):
        self.assertEqual(parse_version("1.2.3rc1"), [1, ".", 2, ".", 3, "rc", 1])

    def test_empty_string_yields_empty_list(self):
        self.assertEqual(parse_version(""), [])

    def test_leading_zeros_normalised(self):
        self.assertEqual(parse_version("007"), [7])
        self.assertEqual(parse_version("007"), parse_version("7"))

    def test_non_string_raises_type_error(self):
        with self.assertRaises(TypeError):
            parse_version(1.0)  # type: ignore[arg-type]

    def test_trailing_separator_kept_as_token(self):
        # A trailing dot is a non-digit run and is preserved, so "1." and "1"
        # are not equal.  This is the documented behaviour.
        self.assertEqual(parse_version("1."), [1, "."])


class CompareVersionsTests(unittest.TestCase):
    def test_numeric_segments_compare_numerically(self):
        # The whole point: 1.10 > 1.9 even though "10" < "9" as strings.
        self.assertGreater(compare_versions("1.10", "1.9"), 0)
        self.assertLess(compare_versions("1.9", "1.10"), 0)

    def test_equal_versions_compare_equal(self):
        self.assertEqual(compare_versions("1.2.3", "1.2.3"), 0)

    def test_prefix_sorts_before_longer(self):
        self.assertLess(compare_versions("1.0", "1.0.1"), 0)
        self.assertLess(compare_versions("1", "1.0"), 0)

    def test_int_sorts_before_string_at_same_position(self):
        # Documented tie-break: at a position where one token is an int and the
        # other a string, the int sorts first.
        self.assertLess(compare_versions("1.2", "1.beta"), 0)
        self.assertGreater(compare_versions("1.beta", "1.2"), 0)

    def test_prerelease_suffix_orders_after_bare_number(self):
        # "1.0" vs "1.0rc1": the second has an extra string token, so the
        # shorter list sorts first.  We state this plainly rather than trying
        # to guess semver prerelease semantics.
        self.assertLess(compare_versions("1.0", "1.0rc1"), 0)

    def test_case_sensitive_string_tokens(self):
        # ASCII ordering: uppercase sorts before lowercase.  No case folding.
        self.assertLess(compare_versions("1.0A", "1.0a"), 0)

    def test_empty_string_is_smallest(self):
        self.assertLess(compare_versions("", "0"), 0)
        self.assertEqual(compare_versions("", ""), 0)


class SortVersionsTests(unittest.TestCase):
    def test_sorts_ascending(self):
        got = sort_versions(["1.10", "1.2", "1.9", "1.0.1", "1.0"])
        self.assertEqual(got, ["1.0", "1.0.1", "1.2", "1.9", "1.10"])

    def test_sort_matches_pairwise_compare(self):
        versions = ["2.0-beta", "2.0", "1.10", "1.9", "1.9.1"]
        ordered = sort_versions(versions)
        for i in range(len(ordered) - 1):
            self.assertLessEqual(compare_versions(ordered[i], ordered[i + 1]), 0)

    def test_empty_input(self):
        self.assertEqual(sort_versions([]), [])


class LooseVersionTests(unittest.TestCase):
    def test_ordering_operators(self):
        self.assertTrue(LooseVersion("1.10") > LooseVersion("1.9"))
        self.assertTrue(LooseVersion("1.0") < LooseVersion("1.0.1"))
        self.assertTrue(LooseVersion("1.2.3") <= LooseVersion("1.2.3"))
        self.assertTrue(LooseVersion("1.2.3") >= LooseVersion("1.2.3"))

    def test_equality_is_token_wise(self):
        self.assertEqual(LooseVersion("1.2.3"), LooseVersion("1.2.3"))
        # Different token counts are not equal even if one is a prefix.
        self.assertNotEqual(LooseVersion("1.0"), LooseVersion("1.0.0"))

    def test_hash_consistent_with_equality(self):
        a = LooseVersion("1.2.3")
        b = LooseVersion("1.2.3")
        self.assertEqual(hash(a), hash(b))
        self.assertEqual(len({a, b}), 1)

    def test_version_and_tokens_properties(self):
        v = LooseVersion("1.2.3rc1")
        self.assertEqual(v.version, "1.2.3rc1")
        self.assertEqual(v.tokens, (1, ".", 2, ".", 3, "rc", 1))

    def test_repr(self):
        self.assertEqual(repr(LooseVersion("1.0")), "LooseVersion('1.0')")

    def test_comparison_with_other_type_is_not_implemented(self):
        with self.assertRaises(TypeError):
            LooseVersion("1.0") < "1.0"  # type: ignore[operator]


if __name__ == "__main__":
    unittest.main()
