#!/usr/bin/env bash
#
# Publish a signed release to Maven Central from this machine.
#
# Usage: ./etc/ci/release.sh X.Y.Z   (or `make release VERSION=X.Y.Z`)
#
# Required secrets (read from the macOS keychain — see SECRETS below):
#   - consequent.sonatype.username
#   - consequent.sonatype.password
#   - consequent.pgp.secret.base64
#   - consequent.pgp.passphrase
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

echo "release: building and testing"
./mill __.compile
./mill test.run

# ---------------------------- SECRETS ----------------------------
#
# Default: macOS keychain. Set the four entries once with:
#   security add-generic-password -a consequent-release \
#     -s consequent.sonatype.username -w 'YOUR_USERNAME'
#   security add-generic-password -a consequent-release \
#     -s consequent.sonatype.password -w 'YOUR_PASSWORD'
#   security add-generic-password -a consequent-release \
#     -s consequent.pgp.secret.base64 -w 'BASE64_PGP_SECRET'
#   security add-generic-password -a consequent-release \
#     -s consequent.pgp.passphrase    -w 'YOUR_PASSPHRASE'
#
# To use a different source, replace `read_secret` below.

read_secret() {
  security find-generic-password -a consequent-release -s "$1" -w 2>/dev/null || {
    echo "release: missing keychain secret '$1'" >&2; exit 1
  }
}

export MILL_SONATYPE_USERNAME
export MILL_SONATYPE_PASSWORD
export MILL_PGP_SECRET_BASE64
export MILL_PGP_PASSPHRASE
MILL_SONATYPE_USERNAME=$(read_secret consequent.sonatype.username)
MILL_SONATYPE_PASSWORD=$(read_secret consequent.sonatype.password)
MILL_PGP_SECRET_BASE64=$(read_secret consequent.pgp.secret.base64)
MILL_PGP_PASSPHRASE=$(read_secret consequent.pgp.passphrase)

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
  --bundleName "dev.propensive-consequent:$VERSION"

trap - ERR
git push origin "refs/tags/$VERSION"

echo "release: published $VERSION"
