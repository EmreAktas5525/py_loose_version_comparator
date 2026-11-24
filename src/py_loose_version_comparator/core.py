"""Compare version strings that do not follow any strict specification.

The strategy is deliberately simple and documented so that callers can rely on
it: a version string is split into a sequence of tokens at every boundary
between a digit run and a non-digit run.  Each token is then classified as
either an integer (a run of ASCII digits) or a string (everything else).

Why this and not semver?  Real-world version strings such as ``1.2.3rc1``,
``2.0-beta``, ``1.0.0+build.5`` or ``2023.10`` all carry meaning that no single
spec captures.  Splitting on the digit/non-digit boundary is the smallest rule
that orders the common cases the way a human reading them expects, and it never
raises on malformed input.

The trade-off: this is not a total order over arbitrary strings.  Two tokens
of different kinds (an int and a string) are ordered by a fixed rule (ints sort
before strings at the same position) rather than by trying to guess intent.
That rule is stated here and tested; it is not negotiable.
"""

from __future__ import annotations

import re
from functools import total_ordering
from typing import Iterable, List, Sequence, Tuple, Union

# A token is either an int (a run of digits) or a str (everything else).
Token = Union[int, str]

# Split at every transition between a digit and a non-digit.  ``re.findall``
# with this pattern yields alternating runs; we keep both kinds because the
# kind matters for comparison.
_TOKEN_RE = re.compile(r"\d+|[^\d]+")


def parse_version(version: str) -> List[Token]:
    """Split *version* into a list of int and str tokens.

    Digit runs become ``int``; every other run stays a ``str``.  An empty
    string yields an empty list, which compares as the smallest possible
    version.  Leading zeros are accepted and normalised by ``int`` (``007``
    and ``7`` are equal), which matches how package managers treat them.

    >>> parse_version("1.2.3rc1")
    [1, '.', 2, '.', 3, 'rc', 1]
    >>> parse_version("")
    []
    """
    if not isinstance(version, str):
        raise TypeError("version must be a str, got %r" % (type(version).__name__,))
    tokens: List[Token] = []
    for part in _TOKEN_RE.findall(version):
        if part.isdigit():
            tokens.append(int(part))
        else:
            tokens.append(part)
    return tokens


def _compare_token(a: Token, b: Token) -> int:
    """Return -1, 0 or 1 comparing two tokens of possibly different kinds.

    Rule: ints sort before strings.  This is the one place where the library
    makes an arbitrary choice; it is documented and tested rather than hidden.
    """
    a_int = isinstance(a, int)
    b_int = isinstance(b, int)
    if a_int and b_int:
        return (a > b) - (a < b)
    if a_int != b_int:
        # int before str
        return -1 if a_int else 1
    # both strings
    return (a > b) - (a < b)


def _compare_token_lists(a: Sequence[Token], b: Sequence[Token]) -> int:
    """Lexicographic comparison with a length tie-break.

    Shorter lists sort first when one is a prefix of the other, so ``1.0``
    sorts before ``1.0.1``.
    """
    for ta, tb in zip(a, b):
        c = _compare_token(ta, tb)
        if c:
            return c
    return (len(a) > len(b)) - (len(a) < len(b))


def compare_versions(a: str, b: str) -> int:
    """Compare two loose version strings.

    Returns a negative number if *a* sorts before *b*, zero if they are equal
    under the loose rules, and a positive number otherwise.
    """
    return _compare_token_lists(parse_version(a), parse_version(b))


def sort_versions(versions: Iterable[str]) -> List[str]:
    """Return *versions* sorted ascending by the loose rules.

    Uses :func:`functools.cmp_to_key` over :func:`compare_versions` so the
    ordering is exactly the same as calling ``compare_versions`` pairwise.
    """
    from functools import cmp_to_key

    return sorted(versions, key=cmp_to_key(compare_versions))


@total_ordering
class LooseVersion:
    """A thin wrapper making loose versions comparable with the usual operators.

    ``LooseVersion("1.2") < LooseVersion("1.10")`` is true, and equality is
    token-wise so ``LooseVersion("1.0") == LooseVersion("1.0.0")`` is false
    (they have different token counts).  That asymmetry is intentional: the
    wrapper reports the same answer as :func:`compare_versions`.
    """

    __slots__ = ("_raw", "_tokens")

    def __init__(self, version: str) -> None:
        self._raw = version
        self._tokens = parse_version(version)

    @property
    def version(self) -> str:
        """The original string passed to the constructor."""
        return self._raw

    @property
    def tokens(self) -> Tuple[Token, ...]:
        """The parsed tokens, as an immutable tuple."""
        return tuple(self._tokens)

    def _key(self) -> Sequence[Token]:
        return self._tokens

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, LooseVersion):
            return NotImplemented
        return _compare_token_lists(self._tokens, other._tokens) == 0

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, LooseVersion):
            return NotImplemented
        return _compare_token_lists(self._tokens, other._tokens) < 0

    def __hash__(self) -> int:
        # Hash the normalised token tuple so equal versions hash equally.
        return hash(tuple(self._tokens))

    def __repr__(self) -> str:
        return "LooseVersion(%r)" % (self._raw,)
