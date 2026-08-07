# Releasing

A release publishes one artifact per supported compiler version, all at the
same version number:

```
dev.propensive:consequent_3.8.4:X.Y.Z
dev.propensive:consequent_3.9.0-RC4:X.Y.Z
```

Publishing runs locally rather than in CI, so the signing key never leaves the
release machine.

## Prerequisites

**The `dev.propensive` namespace must be verified with Sonatype Central**
before the first release. Central verifies ownership of the reversed domain,
so this needs a DNS TXT record on `propensive.dev` — not on `consequent.style`,
which is only the project's website — containing the verification code Central
issues. Until that is done, `make publishLocal` works but `make release` will
be rejected at upload.

Two secrets are read from the macOS keychain — a Central *user token*, not
portal login credentials. Set them once:

```sh
security add-generic-password -a consequent-release \
  -s consequent.sonatype.username -w 'TOKEN_USERNAME'
security add-generic-password -a consequent-release \
  -s consequent.sonatype.password -w 'TOKEN_PASSWORD'
```

To read them from somewhere else — 1Password's CLI, or a gitignored
`.env.release` — replace the `read_secret` function in `etc/ci/release.sh`.

## Signing

The signing key is not one of those secrets. Mill can sign with its own
BouncyCastle implementation, given the exported private key and its passphrase
in `MILL_PGP_SECRET_BASE64` and `MILL_PGP_PASSPHRASE`, but that means an
exported copy of the key and its passphrase both sitting in the environment of
every process the build spawns. Instead `--useGpgCli` tells Mill to shell out
to `gpg`, so the key never leaves `gpg-agent` and the passphrase is entered
through pinentry.

That requires overriding Mill's default `gpgArgs`, which are

```
--no-tty --pinentry-mode loopback --batch --yes --armor --detach-sign
```

`--pinentry-mode loopback` bypasses the agent — it expects the passphrase on
the command line — and `--no-tty` prevents pinentry from drawing anywhere. The
release passes `--batch,--yes,--armor,--detach-sign` instead.

Two consequences for how the release is run:

- **Run it from an interactive terminal.** The script exports `GPG_TTY` and
  calls `gpg-connect-agent updatestartuptty /bye`, which re-points an agent
  started from a different terminal at this one; without it a prompt appears on
  a terminal you cannot see and the release looks like it has hung. Signing
  without a terminal fails with `Inappropriate ioctl for device`.
- **You are prompted once, early.** The script signs a throwaway payload before
  compiling, so a mistyped passphrase costs seconds rather than the whole
  build-and-test cycle, and the agent's cache then covers the artifact signing
  that follows. If the cache expires mid-release, pinentry simply asks again.

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
