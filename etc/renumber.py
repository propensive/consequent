#!/usr/bin/env python3
"""Renumber rule identifiers from the Soundness `SN-nnn` scheme.

Each identifier becomes a principle letter followed by the rule's number within
that principle, numbered in `doc/consequent-style.md` Part II order. Sub-rules
keep a decimal tier.

Applies to string literals (the identifiers the plugin emits) and to comments
(which cite rules by number throughout, including the ordering-constraint block
in `Rules.all` that must stay readable).

Usage: python3 etc/renumber.py
"""

import os
import re

PLUGIN = "src/plugin"

MAPPING = {
  # F — The Frame
  "799": "F1", "131": "F2", "658": "F3", "230": "F4", "135": "F5", "926": "F6",
  "015": "F7", "162": "F8", "162.1": "F8.1", "162.2": "F8.2",

  # A — Anchoring
  "473.1": "A1", "833": "A2", "833.1": "A2.1", "833.2": "A2.2", "833.3": "A3",
  "833.4": "A4", "473.8": "A5", "473.9": "A6", "140": "A7",
  "560": "A8", "560.1": "A8.1", "560.2": "A8.2", "560.3": "A8.3", "560.4": "A8.4",
  "473.2": "A9.1", "473.3": "A9.2", "473.4": "A9.3", "473.5": "A9.4",
  "473.6": "A9.5", "473.7": "A9.6",

  # D — Density
  "247": "D1",
  "312": "D2", "312.1": "D2.1", "312.2": "D2.2", "312.3": "D2.3", "312.4": "D2.4",

  # C — Continuation Marking
  "163": "C1", "163.1": "C1.1", "163.2": "C1.2",
  "616": "C2", "616.1": "C2.1", "616.2": "C2.2", "616.3": "C2.3",
  "444": "C3",

  # B — Balance
  "376": "B1", "376.1": "B2", "013": "B3", "811": "B4", "402": "B5",

  # P — Proximity
  "529": "P1", "529.1": "P1.1", "529.2": "P1.2", "315": "P2", "783": "P3",
  "677": "P4", "441": "P5", "551": "P6", "551.1": "P6.1", "551.2": "P6.2",

  # T — Tabulation
  "326": "T1", "946": "T2",
  "924": "T3", "924.1": "T3.1", "924.2": "T3.2", "924.3": "T3.3", "924.4": "T3.4",

  # L — Locatability
  "302": "L1", "302.1": "L1.1", "302.2": "L1.2", "302.3": "L1.3",
  "847": "L2", "398": "L3", "742": "L4", "742.1": "L5",
}

# The three case-arrow sub-checks emitted non-numeric identifiers with no
# documentation page — they rendered as `[↯SN-R33-multiline-…]`. They are
# sub-checks of `CaseAlignment`, so they become T1.1–T1.3.
LITERAL_MAPPING = {
  "R33-multiline-pattern-arrow-position": "T1.1",
  "R33-multiline-pattern-body-newline":   "T1.2",
  "R33-multiline-case-arrow-space":       "T1.3",
}

# A rule object whose `id` was the first identifier of a multi-identifier family
# should carry the family code, not the first sub-code.
FAMILY_IDS = {"QuoteSpliceLayout": "A9"}

# The pre-SN rule numbering, still cited throughout the comments. Recovered
# from the comments that pair the two schemes (`R30 (811)`, `R12 (402)`, …);
# the rest from the rule each comment describes. `R22`, cited once at
# `AnchorRules.ContinuationIndent` among the bracket-interior rules, is not
# recoverable and that comment is reworded instead.
LEGACY = {
  "R1": "F5", "R2": "F4", "R3": "F6", "R4": "F7", "R6": "P3", "R7": "F2",
  "R9": "L1", "R9.1": "L1.1", "R9.2": "L1.2", "R9.3": "L1.3", "R10": "P5",
  "R11": "P1", "R12": "B5", "R15.2": "P6.2", "R19": "T1", "R20": "P2",
  "R28": "P2", "R29": "L2", "R30": "B4", "R31": "A1", "R32": "A7",
  "R33": "A2", "R33.3": "A3", "R33.4": "A4", "R34": "T3", "R34.3": "T3.3",
  "R36": "T2", "R37": "P1", "R44": "A9",
}

# Longest first, so `833.1` is never matched as `833` followed by `.1`.
ORDERED = sorted(MAPPING, key=len, reverse=True)
ORDERED_LEGACY = sorted(LEGACY, key=len, reverse=True)


def renumber_comment(line: str) -> str:
  """Rewrite bare identifiers in a comment, e.g. `(governed by 924.3)`.

  Restricted to comments because the plugin's own numeric constants (`= 33`,
  `= 100`) live in code and must not be touched. No line or column number
  cited in these comments collides with an identifier.
  """
  for old in ORDERED:
    # The trailing lookahead rejects only a continuing number, so a citation
    # ending a sentence (`… — 473.7.`) or qualified with a wildcard (`833.x`)
    # is still rewritten.
    line = re.sub(rf"(?<![\w.]){re.escape(old)}(?!\.?\d)", MAPPING[old], line)

  return line


def renumber(text: str) -> str:
  for old, new in LITERAL_MAPPING.items():
    text = text.replace(f'"{old}"', f'"{new}"')

  for old in ORDERED:
    new = MAPPING[old]
    # String literals: the identifiers the plugin actually emits.
    text = text.replace(f'"{old}"', f'"{new}"')
    # Comment citations, in all three notations that appear: `SN-833.1`,
    # `R-742`, `R616`. The older `R1`–`R44` scheme predates these codes and is
    # handled separately.
    text = re.sub(rf"\bSN-{re.escape(old)}\b", new, text)
    text = re.sub(rf"\bR-{re.escape(old)}\b", new, text)
    text = re.sub(rf"\bR{re.escape(old)}\b", new, text)

  for old in ORDERED_LEGACY:
    text = re.sub(rf"\b{re.escape(old)}(?!\.?\d)", LEGACY[old], text)

  # Only the comment part of a line: the plugin's numeric constants live in
  # code and must not be touched. A comment need not begin the line — the
  # registry in `Rules.all` opens with `( // …`.
  lines = text.split("\n")
  for index, line in enumerate(lines):
    code, marker, comment = line.partition("//")
    if marker:
      lines[index] = code + marker + renumber_comment(comment)

  text = "\n".join(lines)

  for rule, family in FAMILY_IDS.items():
    pattern = rf'(object {rule} extends Rule:\n    def id: String = )"[^"]*"'
    text = re.sub(pattern, rf'\g<1>"{family}"', text)

  return text


def main() -> None:
  for name in sorted(os.listdir(PLUGIN)):
    if not name.endswith(".scala"):
      continue

    path = os.path.join(PLUGIN, name)
    with open(path, encoding="utf-8") as file:
      text = file.read()

    with open(path, "w", encoding="utf-8") as file:
      file.write(renumber(text))

  print("renumbered")


if __name__ == "__main__":
  main()
