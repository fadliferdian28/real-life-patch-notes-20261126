"""Copy the judged patch-note line to the output directory.

The entry text lives in entry.txt next to this script. This program reads it,
checks it against the embedded sha256/size constants and the competition gate
(UTF-8, 1-160 characters, not whitespace-only, a single line), then writes the
exact bytes to <output>/entry.txt.

Stdlib only. No time, no randomness, no network, fully deterministic.
"""

import hashlib
import os
import shutil
import sys

EXPECTED_SHA256 = "1a157e5f8dda447fd9a30311e71501b84bdf6a0d784d95a3a28cc51a926c5c2a"
EXPECTED_SIZE = 121
MAX_CHARS = 160


def fail(message):
    print("main.py: error: " + message, file=sys.stderr)
    return 1


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    source = os.path.join(here, "entry.txt")

    try:
        with open(source, "rb") as handle:
            data = handle.read()
    except OSError as exc:
        return fail("cannot read %s: %s" % (source, exc))

    if len(data) != EXPECTED_SIZE:
        return fail(
            "entry.txt is %d bytes, expected %d" % (len(data), EXPECTED_SIZE)
        )

    digest = hashlib.sha256(data).hexdigest()
    if digest != EXPECTED_SHA256:
        return fail("entry.txt sha256 mismatch: got %s" % digest)

    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        return fail("entry.txt is not valid UTF-8: %s" % exc)

    line = text.rstrip("\n")
    if "\n" in line or "\r" in line:
        return fail("entry.txt must hold a single line")
    if not (1 <= len(line) <= MAX_CHARS):
        return fail(
            "entry line is %d characters, must be 1-%d" % (len(line), MAX_CHARS)
        )
    if not line.strip():
        return fail("entry line must not be only whitespace")

    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    try:
        os.makedirs(out_dir, exist_ok=True)
    except OSError as exc:
        return fail("cannot create output dir %s: %s" % (out_dir, exc))

    probe = os.path.join(out_dir, ".makefun-write-probe")
    try:
        with open(probe, "wb") as handle:
            handle.write(b"")
        os.remove(probe)
    except OSError as exc:
        return fail("output dir %s is not writable: %s" % (out_dir, exc))

    target = os.path.join(out_dir, "entry.txt")
    try:
        if os.path.exists(target) and os.path.samefile(source, target):
            return fail(
                "output dir is the repo dir itself; refusing to copy "
                "entry.txt onto itself: %s" % target
            )
    except OSError as exc:
        return fail("cannot compare source and target: %s" % exc)
    try:
        shutil.copyfile(source, target)
    except shutil.SameFileError:
        return fail("source and target are the same file: %s" % target)
    except OSError as exc:
        return fail("cannot write %s: %s" % (target, exc))

    with open(target, "rb") as handle:
        written = handle.read()
    if written != data:
        return fail("verification failed: output bytes differ from entry.txt")

    print("wrote %s (%d bytes, %d chars)" % (target, len(data), len(line)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
