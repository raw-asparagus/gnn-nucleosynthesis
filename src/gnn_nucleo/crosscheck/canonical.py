"""Canonical reaction keys for the MESA <-> pynucastro reconciliation.

Convention (stated once, used everywhere; see docs/reaction-reconciliation.md):

* Species names are the project/MESA chem ids (``neut``, ``h1``, ``he4``, ...),
  exactly as in ``configs/isotopes_mesa{80,151}.yaml`` and the Step-3 npz
  ``species`` array. pynucastro ``Nucleus`` objects are mapped fail-loud.
* A *directed key* is ``"<lhs>=><rhs>"`` where each side is the sorted
  reactant/product multiset rendered as ``name*count`` joined by ``+``.
  One directed key == one reaction as evaluated (forward and reverse are
  two different reactions on both sides — MESA softwires them separately
  and pynucastro derives reverse rates as separate Rate objects).
* A *pair key* is the unordered pair of the two sides joined by ``<=>``
  with the lexicographically smaller side first.  It identifies the
  physical link; forward/reverse counting mismatches show up as pair keys
  present on both sides whose directed keys differ.
* Electrons / neutrinos are NOT part of the key: both inventories describe
  weak reactions by their nuclide transition (lhs -> rhs), and lepton
  bookkeeping lives in the constraint matrix C, not in reaction identity.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable

# pynucastro Nucleus.__str__ forms that differ from MESA chem ids
_PYNA_SPECIAL = {
    "n": "neut",
    "p": "h1",
    "d": "h2",
    "t": "h3",
}

# MESA chem ids that differ from a1/z1-style names (fail-loud whitelist;
# isomers such as al26-1/al26-2 are absent from mesa_80/mesa_151 and are
# deliberately NOT mapped)
_MESA_SPECIAL = {
    "prot": "h1",  # MESA distinguishes prot from h1 in some nets
}

_VALID_ELEMENTS = (
    "h he li be b c n o f ne na mg al si p s cl ar k ca sc ti v cr mn fe "
    "co ni cu zn ga ge"
).split()


def _looks_like_iso(name: str) -> bool:
    stem = name.rstrip("0123456789")
    num = name[len(stem):]
    return stem in _VALID_ELEMENTS and num.isdigit()


def from_pyna(nucleus: object) -> str:
    """Map a pynucastro Nucleus (or its str) to a project chem id."""
    s = str(nucleus).lower()
    s = _PYNA_SPECIAL.get(s, s)
    if s != "neut" and not _looks_like_iso(s):
        raise ValueError(f"unmappable pynucastro nucleus: {nucleus!r}")
    return s


def from_mesa(name: str) -> str:
    """Map a MESA chem iso name to a project chem id (fail-loud)."""
    s = name.strip().lower()
    s = _MESA_SPECIAL.get(s, s)
    if s == "neut":
        return s
    if not _looks_like_iso(s):
        raise ValueError(f"unmappable MESA iso name: {name!r}")
    return s


def _side(names: Iterable[str]) -> str:
    """Render a multiset of chem ids as 'a*1+b*2' (sorted)."""
    cnt = Counter(names)
    return "+".join(f"{n}*{cnt[n]}" for n in sorted(cnt))


def directed_key(reactants: Iterable[str], products: Iterable[str]) -> str:
    """Canonical directed reaction key from chem-id multisets."""
    lhs, rhs = _side(reactants), _side(products)
    if not lhs or not rhs:
        raise ValueError("empty reactant or product side")
    return f"{lhs}=>{rhs}"


def pair_key(key: str) -> str:
    """Unordered link key for a directed key."""
    lhs, rhs = key.split("=>")
    a, b = sorted((lhs, rhs))
    return f"{a}<=>{b}"


def reverse_key(key: str) -> str:
    """Directed key of the opposite direction."""
    lhs, rhs = key.split("=>")
    return f"{rhs}=>{lhs}"


def parse_participants(s: str) -> list[str]:
    """Parse the probe dump encoding '1:neut;2:he4' into an expanded
    chem-id list (['neut', 'he4', 'he4'])."""
    out: list[str] = []
    for part in s.split(";"):
        if not part:
            continue
        cf, name = part.split(":")
        out.extend([from_mesa(name)] * int(cf))
    if not out:
        raise ValueError(f"no participants in {s!r}")
    return out
