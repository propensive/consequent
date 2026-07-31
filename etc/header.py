#!/usr/bin/env python3
"""Generate the 32-line Consequent licence header.

The header is exactly 32 lines and 100 columns wide, as required by rules F1
(the block comment must open on line 1 and close on line 32) and F4 (no line
may exceed 100 columns). Line 33 is the `package` declaration (F2).

Run `python3 etc/header.py` to print it; `etc/apply-header.py` rewrites the
header of every source file in place.
"""

WIDTH = 100
YEAR = "2025-26"

WORDMARK = [
  "",
  "",
  "C O N S E Q U E N T",
  "",
  "a syntax and formatting standard for Scala 3",
  "",
]

TEXT = [
  "",
  f"© Copyright {YEAR} Jon Pretty, Propensive OÜ.",
  "",
  "The primary distribution site is:",
  "",
  "    https://consequent.style/",
  "",
  'Licensed under the Apache License, Version 2.0 (the "License"); you may not use this',
  "file except in compliance with the License. You may obtain a copy of the License at",
  "",
  "    https://www.apache.org/licenses/LICENSE-2.0",
  "",
  "Unless required by applicable law or agreed to in writing, software distributed under",
  'the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF',
  "ANY KIND, either express or implied. See the License for the specific language",
  "governing permissions and limitations under the License.",
  "",
]


def framed(content: str) -> str:
  """Wrap `content` in the box, padded to WIDTH columns."""
  return "┃" + content.ljust(WIDTH - 2) + "┃"


def centred(content: str) -> str:
  pad = (WIDTH - 2 - len(content)) // 2
  return framed(" "*pad + content)


def header() -> str:
  lines = ["/*".rjust(WIDTH), "┏" + "━"*(WIDTH - 2) + "┓", framed("")]
  lines += [centred(row) for row in WORDMARK]
  lines += [framed(""), framed("")]
  lines += [framed("   " + row) if row else framed("") for row in TEXT]
  lines += [framed(""), framed("")]
  lines += ["┗" + "━"*(WIDTH - 2) + "┛", "*/".rjust(WIDTH)]

  if len(lines) != 32:
    raise SystemExit(f"header is {len(lines)} lines, expected 32")

  for index, line in enumerate(lines):
    if len(line) > WIDTH:
      raise SystemExit(f"line {index + 1} is {len(line)} columns, expected {WIDTH}")

  return "\n".join(lines)


if __name__ == "__main__":
  print(header())
