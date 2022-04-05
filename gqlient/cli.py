from pathlib import Path
from typing import List, Optional

from typer import Argument, Option, Typer

from gqlient.generator import generate as do_generate

app = Typer()


@app.command()
def generate(schema: str = Argument(..., help="Path to local graphql schema or URL of an API"),
             output: Optional[str] = Option(None, "--output", "-o", help="Output directory"),
             package: Optional[str] = Option(None, "--package", "-p", help="Package name"),
             version: Optional[str] = Option(None, "--version", "-v", help="Package version"),
             description: Optional[str] = Option(None, "--description", "-d", help="Package description"),
             authors: Optional[List[str]] = Option(None, "--authors", "-a", help="Package authors")) -> Optional[str]:
    """
    Generate a standalone client from a GraphQL schema.

    If output is not specified, the generated code will be printed to stdout.

    If package is provided, the generated client will be a buildable Python package.
    Version, description and authors are optional when creating a package.
    """
    if output and not Path(output).exists():
        Path(output).mkdir(parents=True, exist_ok=True)
    result = do_generate(schema, output, package, version, description, authors)
    if not output:
        return result


if __name__ == "__main__":
    app()
