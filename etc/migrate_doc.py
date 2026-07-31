#!/usr/bin/env python3
"""Migrate the standard and the rule documentation into this repository.

Companion to `migrate.py`; run after it. Handles the mechanical part — the
identifier renumbering, the principle renaming, and the substitution of neutral
names for the ones the original examples were drawn from. Passages that discuss
a particular project's idioms are edited by hand afterwards.

Usage: python3 etc/migrate_doc.py [path-to-soundness-checkout]
"""

import os
import re
import sys

from renumber import MAPPING, ORDERED

SOURCE = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/work/soundness")
STANDARD_IN = os.path.join(SOURCE, "doc/standards/syntax.md")
STANDARD_OUT = "doc/consequent-style.md"
ERRORS_IN = os.path.join(SOURCE, "doc/errors")
RULES_OUT = "doc/rules"
PLUGIN = "src/plugin"

# The eight principles, in their document order. `Findability` is renamed
# `Locatability` so that its letter does not collide with `Frame`'s.
PRINCIPLES = [
  ("P1", "F", "The Frame"),
  ("P2", "A", "Anchoring"),
  ("P3", "D", "Density"),
  ("P4", "C", "Continuation Marking"),
  ("P5", "B", "Balance"),
  ("P6", "P", "Proximity"),
  ("P7", "T", "Tabulation"),
  ("P8", "L", "Locatability"),
]

# Library names the original examples were drawn from, mapped to neutral module
# names. The examples are about layout, so the names carry no meaning.
MODULES = {
  "gossamer": "alpha", "anticipation": "beta", "zephyrine": "gamma",
  "jacinta": "delta", "xylophone": "epsilon", "quantitative": "zeta",
  "dissonance": "eta", "stratiform": "theta", "serpentine": "iota",
  "breviloquence": "kappa", "monotonous": "lambda", "turbulence": "mu",
  "mendeleev": "nu", "escritoire": "xi", "honeycomb": "omicron",
  "acyclicity": "pi", "galilei": "rho", "wisteria": "sigma",
  "denominative": "tau", "ambience": "upsilon",
}


def renumber(text: str) -> str:
  """`[SN-833.1]` -> `[A2.1]`, and the same for bare citations."""
  for old in ORDERED:
    new = MAPPING[old]
    text = re.sub(rf"\bSN-{re.escape(old)}(?!\.?\d)", new, text)

  return text


def rename_principles(text: str) -> str:
  """`P1 — The Frame` -> `F — The Frame`, and `**Principle:** P1 …` likewise.

  Done after renumbering, because the Proximity rules are numbered `P1`, `P2`
  and so on, and the principle labels would otherwise collide with them.
  """
  text = text.replace("Findability", "Locatability").replace("findability", "locatability")

  for old, letter, title in PRINCIPLES:
    text = re.sub(rf"\b{old} — {re.escape(title)}", f"{letter} — {title}", text)
    # Roll-calls and cross-references cite the principle by number alone.
    text = re.sub(rf"(?<![\w.])principle {old}(?![\w.])", f"principle {letter}", text)

  return text


def neutralise(text: str) -> str:
  for old, new in MODULES.items():
    text = re.sub(rf"\b{old}\b", new, text)
    text = re.sub(rf"\b{old.capitalize()}\b", new.capitalize(), text)

  return text


# Prose that names the project the standard came from, or bakes in a value
# that is now a plugin option.
PROSE = [
  ("Soundness style", "Consequent Style"),
  ("a documented Soundness convention", "a documented naming convention"),
  ("a documented soundness convention", "a documented naming convention"),
  ("Every Soundness source file", "Every source file"),
  ("Soundness uses a small set of file-name conventions",
   "Consequent Style uses a small set of file-name conventions"),
  ("Soundness reserves block comments", "Consequent Style reserves block comments"),
  ("the `soundness` umbrella package", "the project's umbrella package"),
  ("`import soundness.*` reaches it", "an import of that package reaches it"),
  ("the `soundness` package", "the umbrella package"),
  ("the module's `soundness_*.scala` export list", "the module's export surface"),
  ("exported to `soundness`", "exported to the umbrella package"),
  ("the Decorum compiler plugin", "the Consequences compiler plugin"),
  ("the Decorum checker", "the Consequences checker"),
  ("Decorum", "Consequences"),
]


def convert(text: str) -> str:
  text = rename_principles(renumber(text))
  for old, new in PROSE:
    text = text.replace(old, new)

  return neutralise(text)


def source_link(code: str, owner: dict) -> str:
  """The `See also` section, pointing at the file that defines the rule.

  Every page in the original named one file, and named it wrongly; the map is
  derived from the rule objects themselves so it cannot drift.
  """
  file = owner.get(code)
  lines = ["## See also", "", "- [The standard](../consequent-style.md)"]
  if file is not None:
    lines.append(f"- Source: `src/plugin/{file}`")

  return "\n".join(lines)+"\n"


def rule_owners() -> dict:
  """Map each identifier to the plugin source that defines or emits it."""
  owner = {}
  for name in sorted(os.listdir(PLUGIN)):
    if not name.endswith(".scala"):
      continue

    with open(os.path.join(PLUGIN, name), encoding="utf-8") as file:
      text = file.read()

    for match in re.finditer(r'object \w+ extends Rule:\s*\n\s*def id: String = "([^"]+)"', text):
      owner[match.group(1)] = name

    for match in re.finditer(r'"([A-Z][0-9]+(?:\.[0-9]+)?)"', text):
      owner.setdefault(match.group(1), name)

  return owner


def migrate_standard() -> None:
  with open(STANDARD_IN, encoding="utf-8") as file:
    text = convert(file.read())

  text = text.replace("# Syntax and Formatting", "# Consequent Style", 1)
  text = text.replace("citing its checker identity in `[SN-nnn]`\nform",
                      "citing its checker identity in `[F1]`\nform")

  os.makedirs(os.path.dirname(STANDARD_OUT), exist_ok=True)
  with open(STANDARD_OUT, "w", encoding="utf-8") as file:
    file.write(text)

  print(f"migrated the standard to {STANDARD_OUT}")


def migrate_rules() -> None:
  """Copy the rule pages this plugin raises, renamed to the new identifiers."""
  os.makedirs(RULES_OUT, exist_ok=True)
  owner = rule_owners()
  count = 0

  for old in sorted(MAPPING, key=len, reverse=True):
    path = os.path.join(ERRORS_IN, f"{old}.md")
    if "." in old or not os.path.exists(path):
      continue

    with open(path, encoding="utf-8") as file:
      text = file.read()

    if "Decorum" not in text:
      continue

    code = MAPPING[old]
    text = convert(text)
    text = text.replace("doc/standards/syntax.md", "doc/consequent-style.md")
    text = re.sub(r"## See also\n(?:.|\n)*$", source_link(code, owner), text)

    with open(os.path.join(RULES_OUT, f"{code}.md"), "w", encoding="utf-8") as file:
      file.write(text)

    count += 1

  print(f"migrated {count} rule pages to {RULES_OUT}")


if __name__ == "__main__":
  migrate_standard()
  migrate_rules()
