#!/usr/bin/env bash
#
# Publish a signed release to Maven Central from this machine.
#
# Usage: ./etc/ci/release.sh X.Y.Z   (or `make release VERSION=X.Y.Z`)
#
# Required secrets (read from the macOS keychain — see SECRETS below):
#   - consequent.sonatype.username
#   - consequent.sonatype.password
#
# The signing key is not a secret this script handles: gpg-agent holds it and
# prompts for the passphrase through pinentry. See SIGNING below.
#
# One release publishes every entry of the cross-build — one artifact per
# supported compiler version — all at the same version number.

set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

VERSION="${1:-}"
if [[ -z "$VERSION" ]]; then
  echo "Usage: $0 X.Y.Z" >&2; exit 1
fi
if ! [[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "release: VERSION must be X.Y.Z (got '$VERSION')" >&2; exit 1
fi

# ---------------------------- GUARDS ----------------------------

if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "release: working tree is dirty; commit or stash first" >&2; exit 1
fi

if git rev-parse "refs/tags/$VERSION" >/dev/null 2>&1; then
  echo "release: tag $VERSION already exists locally" >&2; exit 1
fi
if git ls-remote --exit-code --tags origin "refs/tags/$VERSION" >/dev/null 2>&1; then
  echo "release: tag $VERSION already exists on origin" >&2; exit 1
fi

# ---------------------------- SIGNING ----------------------------
#
# The signing key stays in gpg-agent; this script never sees it, and there is
# no exported copy to leak. Mill is told to shell out to `gpg` (`--useGpgCli`)
# rather than use its built-in BouncyCastle signer, which would need the key
# and its passphrase as environment variables.
#
# Mill's default `gpgArgs` are:
#
#   --no-tty --pinentry-mode loopback --batch --yes --armor --detach-sign
#
# `--pinentry-mode loopback` bypasses the agent (it expects the passphrase on
# the command line) and `--no-tty` stops pinentry drawing anywhere. Both are
# dropped here so the agent stays in charge and can prompt.
GPG_ARGS="--batch,--yes,--armor,--detach-sign"

# pinentry needs to know which terminal to prompt on; without this, signing
# fails with "Inappropriate ioctl for device". `updatestartuptty` then points a
# gpg-agent that was started from some *other* terminal at this one — otherwise
# it prompts on a terminal this script cannot see, and appears to hang.
#
# `tty -s` for the test, not `[[ -n $(tty) ]]`: `tty` prints "not a tty" on
# stdout and signals through its exit status, so capturing its output always
# yields a non-empty string.
if tty -s; then
  GPG_TTY=$(tty)
  export GPG_TTY
  gpg-connect-agent updatestartuptty /bye >/dev/null 2>&1 || true
else
  # Not fatal: a graphical pinentry needs no terminal, and a warm agent cache
  # needs no prompt at all. The signing check below is the real gate.
  echo "release: no controlling terminal; gpg can only sign if it need not prompt" >&2
fi

# Unlock the key *before* the build rather than after it: a mistyped passphrase
# should cost seconds, not the whole compile-and-test cycle. This also warms the
# agent's cache, so signing the artifacts later need not prompt again.
echo "release: unlocking the signing key (gpg may prompt)"
if ! printf 'release' \
     | gpg --batch --yes --armor --detach-sign --output /dev/null 2>/dev/null; then
  echo "release: gpg could not sign; check the key is present and the passphrase correct" >&2
  exit 1
fi

echo "release: building and testing"
./mill __.compile
./mill test.run

# ---------------------------- SECRETS ----------------------------
#
# Default: macOS keychain. Set the two entries once with:
#   security add-generic-password -a consequent-release \
#     -s consequent.sonatype.username -w 'YOUR_USERNAME'
#   security add-generic-password -a consequent-release \
#     -s consequent.sonatype.password -w 'YOUR_PASSWORD'
#
# These are a Central *user token*, not portal login credentials.
#
# To use a different source, replace `read_secret` below.

read_secret() {
  security find-generic-password -a consequent-release -s "$1" -w 2>/dev/null || {
    echo "release: missing keychain secret '$1'" >&2; exit 1
  }
}

export MILL_SONATYPE_USERNAME
export MILL_SONATYPE_PASSWORD
MILL_SONATYPE_USERNAME=$(read_secret consequent.sonatype.username)
MILL_SONATYPE_PASSWORD=$(read_secret consequent.sonatype.password)

# ---------------------------- TAG ----------------------------
#
# Tagged before publishing so that `publishVersion`'s `git describe` fallback
# agrees with the version being released; deleted again if publishing fails.

git tag -s "$VERSION" -m "Version $VERSION"
trap 'git tag -d "$VERSION" >/dev/null 2>&1 || true' ERR

# `Task.env`, not `sys.env`: the Mill daemon captures `sys.env` at startup, so
# a long-running daemon would otherwise publish a stale version.
export CONSEQUENT_RELEASE_VERSION="$VERSION"

for module in $(./mill resolve 'consequent[_]'); do
  actual=$(./mill show "$module.publishVersion" | tr -d '"')
  if [[ "$actual" != "$VERSION" ]]; then
    echo "release: $module reports version '$actual', expected '$VERSION'" >&2; exit 1
  fi
done

# ---------------------------- PUBLISH ----------------------------

./mill mill.javalib.SonatypeCentralPublishModule/publishAll \
  --publishArtifacts '__.publishArtifacts' \
  --shouldRelease true \
  --useGpgCli true \
  --gpgArgs "$GPG_ARGS" \
  --bundleName "dev.propensive-consequent:$VERSION"

trap - ERR
git push origin "refs/tags/$VERSION"

echo "release: published $VERSION"
