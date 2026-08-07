.PHONY: build test publishLocal release clean

# Compile the plugin against every supported compiler version.
build:
	./mill __.compile

# Run the test suite. It builds against one compiler version only; see the
# comment on `testScalaVersion` in `build.mill`.
test:
	./mill test.run

# Usage: make publishLocal VERSION=X.Y.Z
publishLocal:
	@if [ -z "$(VERSION)" ]; then echo "Usage: make publishLocal VERSION=X.Y.Z" >&2; exit 1; fi
	CONSEQUENT_RELEASE_VERSION="$(VERSION)" ./mill __.publishLocal

# Usage: make release VERSION=X.Y.Z
release:
	@if [ -z "$(VERSION)" ]; then echo "Usage: make release VERSION=X.Y.Z" >&2; exit 1; fi
	./etc/ci/release.sh "$(VERSION)"

clean:
	./mill clean
