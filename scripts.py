from dataclasses import dataclass

import asyncio
import concurrent.futures
import glob
import argparse
import subprocess
import sys
from typing import Callable, Optional


@dataclass
class Args:
    program: str
    command: Optional[str] = None
    file: Optional[str] = None
    glob: Optional[str] = None
    recursive: Optional[bool] = False
    dev: Optional[bool] = False
    parser: Optional[argparse.ArgumentParser] = None
    func: Optional[Callable] = None


def cmd_run(args, **kwargs):
    print(f"CMD: '{' '.join(args)}'")
    subprocess.run(args, **kwargs)


def format_file(file):
    cmd_run(["autopep8", "--in-place", "--aggressive", file], check=True)
    cmd_run(["isort", file], check=True)


async def format_file_glob(expr, **kwargs):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(lambda file: format_file(file), glob.glob(expr, **kwargs))


async def format_files():
    await asyncio.gather(
        format_file_glob("*.py"),
        format_file_glob("server/**/*.py", recursive=True),
        format_file_glob("tests/**/*.py", recursive=True)
    )


async def command_format(args: Args) -> None:
    "Format all python files"
    if args.glob is not None:
        await format_file_glob(args.glob, recursive=args.recursive)
    elif args.file is not None:
        await format_file(args.file)
    else:
        await format_files()


async def command_run(args: Args) -> None:
    "Run the server"
    if args.dev:
        cmd_run(["uvicorn", "api:app", "--log-config", "logging_config.ini", "--reload"])
    else:
        cmd_run(["uvicorn", "api:app", "--log-config", "logging_config.ini"])


async def command_venv(_args: Args) -> None:
    "Create a virtual environment"
    cmd_run(["python", "-m", "venv", "venv"])


async def command_tip(_args: Args) -> None:
    "Show some tips"

    print("# 1. To create a virtual environment, run:")
    print()
    print("python3 -m venv venv")
    print("# or:")
    print("python scripts.py venv")
    print()
    print()
    print("# 2. To activate the virtual environment, run:")
    print()
    print("# For linux:")
    print("source venv/bin/activate")
    print()
    print("# For windows powershell:")
    print(".\\venv\\Scripts\\Activate.ps1")
    print()
    print()
    print("# 3. To install dependencies, run:")
    print()
    print("pip install -r requirements.txt")
    print("# or:")
    print("python scripts.py install")
    print()
    print()
    print("# 4. To run the server, run:")
    print()
    print("# In production:")
    print("uvicorn api:app --log-config logging_config.ini")
    print("# or:")
    print("python scripts.py run")
    print()
    print("# In development:")
    print("uvicorn api:app --log-config logging_config.ini --reload")
    print("# or:")
    print("python scripts.py run --dev")
    print()


async def command_install(args: Args) -> None:
    "Install dependencies"
    cmd_run(["pip", "install", "-r", "requirements.txt"])
    if args.dev:
        cmd_run(["pip", "install", "-r", "requirements-dev.txt"])


async def command_check_types(_args: Args) -> None:
    "Check types with mypy"
    cmd_run(["mypy", "."])


async def command_test(_args: Args) -> None:
    "Run tests"
    cmd_run(["pytest", "tests/"])


def parse_args():
    def from_command(func: Callable) -> argparse.ArgumentParser:
        prefix = "command_"
        name = func.__name__.replace(prefix, "")
        name = name.replace("_", "-")
        sp = subparser.add_parser(name, help=func.__doc__)
        sp.set_defaults(func=func)
        return sp

    parser = argparse.ArgumentParser()
    subparser = parser.add_subparsers(dest="command")

    sp = from_command(command_run)
    sp.add_argument('--dev', action='store_true', help="Run in development mode")

    sp = from_command(command_format)
    sp.add_argument('--file', '-f', help="Format a single file")
    sp.add_argument('--glob', '-g', help="Format a glob expression")
    sp.add_argument('--recursive', '-r', action='store_true', help="Format recursively")

    sp = from_command(command_check_types)

    sp = from_command(command_tip)

    sp = from_command(command_test)

    sp = from_command(command_venv)

    sp = from_command(command_install)

    options, args = parser.parse_known_args()
    args = Args(
        program=sys.argv[0],
        parser=parser,
        **vars(options)
    )
    return args

async def main():
    args = parse_args()
    if args.command is None:
        args.parser.print_help()
    else:
        await args.func(args)

if __name__ == "__main__":
    asyncio.run(main())
