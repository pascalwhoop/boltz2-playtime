import typer
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from .commands import generate  # noqa: E402

app = typer.Typer()

app.add_typer(generate.app, name="generate")
