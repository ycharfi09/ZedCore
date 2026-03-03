"""CLI entry point for `zrun` / `python -m zedcore`."""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .runtime import run_file, Runtime


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="zrun",
        description=f"ZedCore language runtime v{__version__}",
    )
    parser.add_argument("file", nargs="?", help="ZedCore source file to run")
    parser.add_argument(
        "--no-retro",
        action="store_true",
        default=False,
        help="Suppress retrograde pass output",
    )
    parser.add_argument(
        "--version", "-V",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "--lex",
        action="store_true",
        help="Print tokens only (debug)",
    )
    parser.add_argument(
        "--parse",
        action="store_true",
        help="Print AST only (debug)",
    )

    args = parser.parse_args(argv)

    if args.file is None:
        parser.print_help()
        return 0

    try:
        if args.lex:
            from .lexer import Lexer
            with open(args.file, encoding="utf-8") as fh:
                source = fh.read()
            tokens = Lexer(source).tokenize()
            for tok in tokens:
                print(tok)
            return 0

        if args.parse:
            from .lexer import Lexer
            from .parser import Parser
            import pprint
            with open(args.file, encoding="utf-8") as fh:
                source = fh.read()
            tokens = Lexer(source).tokenize()
            program = Parser(tokens).parse()
            pprint.pprint(program)
            return 0

        return run_file(args.file, print_retro=not args.no_retro)
    except FileNotFoundError:
        sys.stderr.write(f"zrun: file not found: {args.file!r}\n")
        return 1
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
