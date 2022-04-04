from pathlib import Path
from typing import Optional

from typer import Option, Typer

from gqlient.generator import generate as do_generate

app = Typer()


@app.command()
def generate(schema: str,
             output: Optional[str] = Option(None, "--output", "-o", help="Output file")):
    if output and not Path(output).exists():
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        Path(output).touch()
    result = do_generate(schema, output)
    if not output:
        return result


if __name__ == "__main__":
    app()
