#!/usr/bin/env python3
"""One-shot migration of the Decorum plugin sources into this repository.

Copies every plugin source from a Soundness checkout, replaces the 32-line
licence header, and applies the Decorum -> Consequences renaming. Kept in the
repository so the migration is reproducible and auditable, but it is not part
of the build.

Usage: python3 etc/migrate.py [path-to-soundness-checkout]
"""

import os
import re
import sys

from header import header

SOURCE = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/work/soundness")
PLUGIN_IN = os.path.join(SOURCE, "lib/decorum/src/plugin")
PLUGIN_OUT = "src/plugin"

# `soundness_decorum_plugin.scala` is a `package soundness` re-export surface
# that exists only to satisfy Soundness's own umbrella-export rule.
SKIP = {"soundness_decorum_plugin.scala"}

# Applied in order. `Findability` -> `Locatability` also rewrites the
# `FindabilityRules` object and its file name, so it must precede nothing in
# particular, but the more specific names must precede the general ones.
RENAMES = [
  (r"\bSoundnessExportCompleteness\b", "UmbrellaExportCompleteness"),
  (r"\bSoundnessExports\b", "UmbrellaExports"),
  (r"\bsoundnessSiblingModules\b", "umbrellaSiblingModules"),
  (r"\bsoundnessSiblingExtensions\b", "umbrellaSiblingExtensions"),
  (r"\bsoundnessSiblingSurfaceExports\b", "umbrellaSiblingSurfaceExports"),
  (r"\bsoundnessUnexported\b", "umbrellaUnexported"),
  (r"\bsoundnessExports\b", "umbrellaExports"),
  (r"\bFindability\b", "Locatability"),
  (r"\bDecorumPlugin\b", "ConsequencesPlugin"),
  (r"\bDecorumPhase\b", "ConsequencesPhase"),
  (r"\bDecorum\b", "Consequences"),
  (r"\bdecorum\b", "consequences"),
  (r"doc/standards/syntax\.md", "doc/consequent-style.md"),
]

FILE_RENAMES = \
  { "FindabilityRules": "LocatabilityRules",
    "SoundnessExports": "UmbrellaExports",
    "DecorumPlugin":    "ConsequencesPlugin",
    "DecorumPhase":     "ConsequencesPhase" }


def rename_file(name: str) -> str:
  """`decorum.FindabilityRules.scala` -> `consequences.LocatabilityRules.scala`."""
  stem = name[len("decorum."):-len(".scala")]
  return f"consequences.{FILE_RENAMES.get(stem, stem)}.scala"


def migrate(text: str) -> str:
  body = text.split("\n")[32:]
  out = header() + "\n" + "\n".join(body)
  for pattern, replacement in RENAMES:
    out = re.sub(pattern, replacement, out)

  return out


def main() -> None:
  os.makedirs(PLUGIN_OUT, exist_ok=True)
  count = 0
  for name in sorted(os.listdir(PLUGIN_IN)):
    if not name.endswith(".scala") or name in SKIP:
      continue

    with open(os.path.join(PLUGIN_IN, name), encoding="utf-8") as file:
      text = file.read()

    with open(os.path.join(PLUGIN_OUT, rename_file(name)), "w", encoding="utf-8") as file:
      file.write(migrate(text))

    count += 1

  print(f"migrated {count} plugin sources")


if __name__ == "__main__":
  main()
