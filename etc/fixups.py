#!/usr/bin/env python3
"""Hand-authored edits to the standard, applied after `migrate_doc.py`.

The mechanical passes rename identifiers; these passages needed judgement.
Each rewrites an example that was drawn from the project the standard came
from, keeping the layout being illustrated and replacing the vocabulary with
stdlib equivalents — or, where the example is *about* a project-specific
facility, restating it as the category with a pointer to the option that
configures it.

Usage: python3 etc/fixups.py
"""

import pathlib

Q = '"""'

APPENDIX_C_OLD = f'''The string interpolators in general use are:

- `t"…"` for `Text`.
- `m"…"` for `Message`.
- `s"…"` and plain `"…"` only where a raw `String` is genuinely needed.

Five interpolators produce values on which the leading and trailing
whitespace of the literal has no effect:

| Prefix | Content  |
| ------ | -------- |
| `m`    | messages |
| `j`    | JSON     |
| `x`    | XML      |
| `y`    | YAML     |
| `tel`  | TEL      |

Because their whitespace is insignificant, their multi-line `{Q}…{Q}`
literals can be — and must be — laid out as indented blocks ([A8],
A). Every other interpolator (`t`, `s`, `sh`, …) and raw `{Q}` string
carries significant whitespace, so the layout of its content is left
entirely to the author, and the line-length and trailing-whitespace rules
do not apply to the interior of any multi-line string.'''

APPENDIX_C_NEW = f'''Some interpolators produce values on which the leading and trailing
whitespace of the literal has no effect — an interpolator for structured data
such as JSON, XML or YAML is the usual case, because the whitespace is
discarded by the parse.

Because their whitespace is insignificant, their multi-line `{Q}…{Q}`
literals can be — and must be — laid out as indented blocks ([A8], A). Every
other interpolator, and every raw `{Q}` string, carries significant
whitespace, so the layout of its content is left entirely to the author, and
the line-length and trailing-whitespace rules do not apply to the interior of
any multi-line string.

A project declares its whitespace-insignificant interpolators to the checker
by prefix, so the checker knows which literals it may govern:

```
-P:consequences:interpolators=m,j,x,y
```'''

# The two block-string examples used a message interpolator; `j` (JSON) is a
# clearer instance of the category the section is actually about.
MESSAGE_BLOCK_OLD = f'''def message =
  m{Q}
    This is the message.
    It spans two lines.
  {Q}'''

MESSAGE_BLOCK_NEW = f'''def document =
  j{Q}
    {{ "kind": "example",
      "lines": 2 }}
  {Q}'''

HEAVY_BLOCK_OLD = f'''extends Error
  ( m{Q}
      the table required a minimum width of $minimumWidth, but only $availableWidth was available
    {Q} )'''

HEAVY_BLOCK_NEW = f'''extends Failure
  ( m{Q}
      the table required a minimum width of $minimumWidth, but only $availableWidth was available
    {Q} )'''

SUBS = [
  (APPENDIX_C_OLD, APPENDIX_C_NEW),
  (MESSAGE_BLOCK_OLD, MESSAGE_BLOCK_NEW),
  (HEAVY_BLOCK_OLD, HEAVY_BLOCK_NEW),
  ('case CannotSwitchBranch => m"the branch could not be changed"',
   'case CannotSwitchBranch => "the branch could not be changed"'),
  ('case CannotExecuteGit   => m"the `git` command could not be executed"',
   'case CannotExecuteGit   => "the `git` command could not be executed"'),
  ('case CloneFailed        => m"the repository could not be cloned"',
   'case CloneFailed        => "the repository could not be cloned"'),
  ('case InvalidRepoPath    => m"the repository path was not valid"',
   'case InvalidRepoPath    => "the repository path was not valid"'),
  ('  `StringContext` (every `t"…"`-style interpolator), a collection (`List`,',
   '  `StringContext` (every custom interpolator), a collection (`List`,'),
  ("top level uncluttered. `eta.Diff`, `gamma.Cursor` and\n`theta.Tel` follow this.",
   "top level uncluttered."),
  ("cannot add to `theta.core`'s `object Tel`.)",
   "cannot add to a companion defined in `theta.core`.)"),
  ("`def`s (see `delta.Json.parseTracked`). A `Dynamic` **value class** does\n"
   "  *not* have this problem — `tel.edited` still resolves to a companion\n"
   "  extension even though `class Tel extends Dynamic`.",
   "`def`s. A `Dynamic` **value class** does *not* have this problem: a\n"
   "  companion extension still resolves on it."),
  ("§\"Comma-column alignment\").", "\"Comma-column alignment\" below)."),
]


def main() -> None:
  path = pathlib.Path("doc/consequent-style.md")
  text = path.read_text(encoding="utf-8")

  for old, new in SUBS:
    if old not in text:
      print(f"  no match: {old[:60]!r}")
      continue

    text = text.replace(old, new)

  path.write_text(text, encoding="utf-8")
  print("applied fixups")


if __name__ == "__main__":
  main()
