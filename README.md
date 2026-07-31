# Consequent

**Consequent Style** is a syntax and formatting standard for Scala 3, and
**Consequences** is the compiler plugin that enforces it.

Most formatting standards describe an output: run the formatter, accept what it
produces. Consequent Style instead states eight *principles* about how code is
read, and derives its rules from them. The rules are checked, not applied —
there is no reformatter — because several of them (where to break a long
signature, which of two shapes fits a definition) have more than one correct
answer, and the choice belongs to the author.

- [The standard](doc/consequent-style.md)
- [Rule reference](doc/rules/)
- [Releasing](doc/releasing.md)

## The eight principles

| | Principle | Concern |
| --- | --- | --- |
| **F** | The Frame | the fixed shape every file sits in |
| **A** | Anchoring | where a continuation line begins |
| **D** | Density | how much to fit on one line |
| **C** | Continuation Marking | showing that a line is unfinished |
| **B** | Balance | symmetry of spacing around a token |
| **P** | Proximity | blank lines and gaps as grouping |
| **T** | Tabulation | vertical alignment across a run of lines |
| **L** | Locatability | finding a definition from its name |

Every rule carries an identifier of the form `F1`, `A2.3` — the principle it
derives from, then its number within that principle. Each has a page under
[`doc/rules/`](doc/rules/).

## Using the plugin

Consequences is published for each supported Scala compiler version, because a
compiler plugin links against compiler internals:

```
style.consequent:consequences_3.8.4
style.consequent:consequences_3.9.0-RC4
```

Add it as a compiler plugin. With Mill:

```scala
def scalacPluginMvnDeps = Seq(mvn"style.consequent:consequences_${scalaVersion()}:$version")
```

By default violations are reported as warnings; `-P:consequences:errors` makes
them errors.

### Options

| Option | Default | Meaning |
| --- | --- | --- |
| `errors` | off | report violations as errors rather than warnings |
| `header=<n>` | `32` | number of lines in the licence header (`0` disables `F1`) |
| `columns=<n>` | `100` | maximum line length |
| `umbrella=<pkg>` | unset | umbrella re-export package; unset disables `L4` and `L5` |
| `moduleRoot=<seg>` | `lib` | path segment below which each module has its own directory |
| `language=<f,…>` | per compiler | `-language` features to enable when parsing |
| `interpolators=<i,…>` | `s,f,raw` | interpolators whose interior whitespace is significant |

## Building

Requires JDK 21+. Everything else is fetched by the `./mill` bootstrap.

```
make build     # compile both cross-versions
make test      # run the test suite
```

## License

Consequent is made available under the [Apache 2.0 License](LICENSE).
