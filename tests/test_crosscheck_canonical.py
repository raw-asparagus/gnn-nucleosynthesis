"""Unit tests for the reconciliation canonicalization layer.

These are pure-function tests (no MESA, no pynucastro network build); they
pin the naming convention BEFORE any diff is trusted (Step-4 brief, Task 1).
"""

import pytest

from gnn_nucleo.crosscheck import (
    directed_key,
    from_mesa,
    from_pyna,
    pair_key,
    parse_participants,
    reverse_key,
)


class TestNameMapping:
    def test_pyna_specials(self):
        assert from_pyna("n") == "neut"
        assert from_pyna("p") == "h1"
        assert from_pyna("d") == "h2"
        assert from_pyna("t") == "h3"

    def test_pyna_case_folding(self):
        assert from_pyna("He4") == "he4"
        assert from_pyna("Ni56") == "ni56"

    def test_mesa_specials(self):
        assert from_mesa("neut") == "neut"
        assert from_mesa("prot") == "h1"
        assert from_mesa(" fe56 ") == "fe56"

    def test_unknown_names_fail_loud(self):
        with pytest.raises(ValueError):
            from_mesa("al-6")  # isomer: not mappable, must not pass silently
        with pytest.raises(ValueError):
            from_pyna("xx99")


class TestKeys:
    def test_permutation_invariance(self):
        k1 = directed_key(["neut", "al25"], ["al26"])
        k2 = directed_key(["al25", "neut"], ["al26"])
        assert k1 == k2 == "al25*1+neut*1=>al26*1"

    def test_multiset_counts(self):
        k = directed_key(["he4", "he4", "he4"], ["c12"])
        assert k == "he4*3=>c12*1"

    def test_direction_distinguishes(self):
        f = directed_key(["neut", "al25"], ["al26"])
        r = directed_key(["al26"], ["neut", "al25"])
        assert f != r
        assert reverse_key(f) == r
        assert pair_key(f) == pair_key(r)

    def test_pair_key_ordering_stable(self):
        f = directed_key(["he4", "ca40"], ["ti44"])
        assert pair_key(f) == pair_key(reverse_key(f))
        lhs, rhs = pair_key(f).split("<=>")
        assert lhs < rhs

    def test_empty_side_rejected(self):
        with pytest.raises(ValueError):
            directed_key([], ["c12"])


class TestParticipantParsing:
    def test_round_trip_with_directed_key(self):
        ins = parse_participants("1:neut;1:al25")
        outs = parse_participants("1:al26")
        assert directed_key(ins, outs) == "al25*1+neut*1=>al26*1"

    def test_coefficients_expand(self):
        assert parse_participants("2:he4") == ["he4", "he4"]
        assert parse_participants("1:h1;2:he4") == ["h1", "he4", "he4"]

    def test_prot_maps_to_h1(self):
        assert parse_participants("1:prot") == ["h1"]

    def test_empty_fails(self):
        with pytest.raises(ValueError):
            parse_participants("")
