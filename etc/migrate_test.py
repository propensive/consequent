#!/usr/bin/env python3
"""Migrate the Decorum test suite into this repository.

Companion to `migrate.py`; run after it. The suite is ported nearly verbatim —
its value is that it pins the behaviour of every rule — so this applies the same
renaming and renumbering plus the handful of changes the new APIs require.

Usage: python3 etc/migrate_test.py [path-to-soundness-checkout]
"""

import os
import re
import sys

from header import header
from renumber import LITERAL_MAPPING, MAPPING, ORDERED

SOURCE = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/work/soundness")
TEST_IN = os.path.join(SOURCE, "lib/decorum/src/test/decorum_test.scala")
TEST_OUT = "src/test/consequences_test.scala"

# The fixtures use real library names purely as sample import paths. They read
# oddly in a standalone repository, so they become neutral module names.
MODULES = {
  "gossamer": "alpha", "anticipation": "beta", "zephyrine": "gamma",
  "jacinta": "delta", "xylophone": "epsilon",
}

RENAMES = [
  (r'Suite\(m"Decorum Tests"\)', 'Suite(m"Consequences Tests")', 0),
  (r"\bdecorum\b", "consequences", 0),
  (r"\bDecorum\b", "Consequences", 0),
]

# `import soundness.*` pulls in the whole Soundness world through one umbrella.
# Depend on the pieces the suite actually uses instead. Substituted after the
# fixture names are neutralised, so the real module names here survive.
IMPORTS = "import probably.*\nimport fulminate.*\nimport gossamer.*"


def renumber(text: str) -> str:
  # Test names cite rules in prose too, not only in the assertions.
  for old in ORDERED:
    text = text.replace(f"SN-{old}", MAPPING[old])

  for old, new in LITERAL_MAPPING.items():
    text = text.replace(f'"{old}"', f'"{new}"')

  for old in ORDERED:
    text = text.replace(f'"{old}"', f'"{MAPPING[old]}"')

  return text


def neutralise(text: str) -> str:
  for old, new in MODULES.items():
    text = re.sub(rf"\b{old}\b", new, text)

  return text


def migrate(text: str) -> str:
  body = "\n".join(text.split("\n")[32:])
  for pattern, replacement, flags in RENAMES:
    body = re.sub(pattern, replacement, body, flags=flags)

  body = neutralise(renumber(body))
  body = re.sub(r"^import soundness\.\*$", IMPORTS, body, flags=re.MULTILINE)

  return header() + "\n" + body


def main() -> None:
  with open(TEST_IN, encoding="utf-8") as file:
    text = file.read()

  os.makedirs(os.path.dirname(TEST_OUT), exist_ok=True)
  with open(TEST_OUT, "w", encoding="utf-8") as file:
    file.write(migrate(text))

  print(f"migrated the test suite to {TEST_OUT}")


if __name__ == "__main__":
  main()
