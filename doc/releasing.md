# Releasing

A release publishes one artifact per supported compiler version, all at the
same version number:

```
style.consequent:consequences_3.8.4:X.Y.Z
style.consequent:consequences_3.9.0-RC4:X.Y.Z
```

Publishing runs locally rather than in CI, so the signing key never leaves the
release machine.

## Prerequisites

**The `style.consequent` namespace must be verified with Sonatype Central**
before the first release. Central verifies ownership of the reversed domain,
so this needs a DNS TXT record on `consequent.style` containing the
verification code Central issues. Until that is done, `make publishLocal`
works but `make release` will be rejected at upload.

Four secrets are read from the macOS keychain. Set them once:

```sh
security add-generic-password -a consequent-release \
  -s consequent.sonatype.username -w 'USERNAME'
security add-generic-password -a consequent-release \
  -s consequent.sonatype.password -w 'PASSWORD'
security add-generic-password -a consequent-release \
  -s consequent.pgp.secret.base64 -w 'BASE64_PGP_SECRET'
security add-generic-password -a consequent-release \
  -s consequent.pgp.passphrase    -w 'PASSPHRASE'
```

To read them from somewhere else — 1Password's CLI, or a gitignored
`.env.release` — replace the `read_secret` function in `etc/ci/release.sh`.

## Releasing

```sh
make release VERSION=X.Y.Z
```

The script refuses to run on a dirty tree, or when the tag already exists
locally or on `origin`. It then compiles every cross-version, runs the test
suite, creates a signed tag, checks that each module reports the version being
released, uploads the bundle to Central, and pushes the tag.

If publishing fails the tag is deleted again, so the command can be retried
once the cause is fixed.

## How the version reaches the build

`publishVersion` reads `CONSEQUENT_RELEASE_VERSION` through Mill's `Task.env`,
not `sys.env`. This matters: the Mill daemon captures `sys.env` when it starts,
so a daemon left running from before the variable was exported would publish
the version it started with. Outside a release the version falls back to
`git describe`.

## Adding a compiler version

Add it to `scalaVersions` in `build.mill`. If it needs different sources — the
`StandardPlugin.initialize` signature changed in 3.5, so anything older needs a
shim — add `src/compat/scala-<version>` and wire it into
`sources`.

Check first that the plugin still compiles: it links against compiler
internals, and `dotty.tools.dotc.ast.untpd` tree shapes are the largest surface
area. The test suite is the regression gate.
