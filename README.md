# dupefind

Small pure-stdlib Python 3 CLI that finds duplicate files in a directory tree.
Files are grouped by size, then confirmed by sha256. Simple `.gitignore`
patterns from the root are honored (fnmatch globs, `dir/` patterns, `#` comments;
negation `!` is not supported and is skipped).

## Install

No dependencies. Copy `dupefind.py` or run it in place.

## Usage

    python3 dupefind.py [ROOT] [--min-size N] [--json] [--delete-hint]

- `--min-size N`  ignore files smaller than N bytes (default 1)
- `--json`        machine-readable output
- `--delete-hint` print `rm` commands for all but the first file in each group.
  It never deletes anything; review the output before running it.

Example:

    $ python3 dupefind.py photos --min-size 1024
    2cf24dba5fb0  5 bytes
      photos/a.txt
      photos/sub/b.txt

    $ python3 dupefind.py photos --delete-hint
    # keep photos/a.txt
    rm -- photos/sub/b.txt

## Tests

    python3 -m unittest

## License

MIT
