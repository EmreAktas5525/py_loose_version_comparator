# py_loose_version_comparator

Compare version strings that follow no strict specification by splitting each
string at every digit/non-digit boundary and comparing the resulting tokens.

```python
from py_loose_version_comparator import (
    LooseVersion,
    compare_versions,
    parse_version,
    sort_versions,
)

compare_versions("1.10", "1.9")        # > 0, because 10 > 9
compare_versions("1.0", "1.0.1")       # < 0, prefix sorts first
parse_version("1.2.3rc1")              # [1, '.', 2, '.', 3, 'rc', 1]
sort_versions(["1.10", "1.2", "1.9"]) # ['1.2', '1.9', '1.10']
LooseVersion("2.0") > LooseVersion("2.0-beta")  # True
```

## Why this exists

Version strings in the wild are not semver.  They are `1.2.3rc1`, `2.0-beta`,
`1.0.0+build.5`, `2023.10`, `1.0a`.  Package managers each invent their own
rules.  This library picks the smallest rule that gets the common cases right:
split on digit/non-digit boundaries, turn digit runs into `int`, and compare
token by token.

The trade-off is that this is not a total order over arbitrary strings.  Two
arbitrary strings with different token kinds at the same position are ordered
by a fixed rule rather than by guessing intent: **an integer token sorts before
a string token at the same position**.  So `1.2 < 1.beta`.  That rule is stated
here and covered by tests; it is not negotiable.

## The awkward edge

A shorter version that is a prefix of a longer one sorts first.  So `1.0`
compares less than `1.0.1`, and also less than `1.0rc1`, because `1.0rc1` has an
extra token.  If you were expecting semver's prerelease ordering (where `1.0rc1`
would come *before* `1.0`), this library does not do that.  It does one thing:
lexicographic comparison of token lists.  Pick a different rule if you need
semver.

Equality is token-wise as well, so `LooseVersion("1.0") != LooseVersion("1.0.0")`
even though the former sorts before the latter.  That is consistent with
`compare_versions`.

## API

- `parse_version(version: str) -> list[int | str]` — split into tokens.
- `compare_versions(a: str, b: str) -> int` — negative, zero, or positive.
- `sort_versions(versions) -> list[str]` — ascending, same order as
  `compare_versions` pairwise.
- `LooseVersion(version: str)` — wrapper with `<`, `<=`, `==`, `>=`, `>`,
  `!=`, and `hash`.  Exposes `.version` (original string) and `.tokens`
  (tuple of parsed tokens).
