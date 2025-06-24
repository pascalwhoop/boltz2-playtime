import os
from pathlib import Path
from typing import Optional

import requests
import typer
import yaml

from boltz_2_bindings.tools.identifier_mapping import (
    get_pubchem_smiles_from_drugbank,
)

app = typer.Typer(help="Generate related commands.")
# Define constants for URLs
DRUGBANK_API_URL_TEMPLATE = "https://api.drugbank.com/discovery/v1/drugs/{}"
UNIPROT_API_TEMPLATE = "https://rest.uniprot.org/uniprotkb/{}.json"

DRUGBANK_API_KEY = os.getenv("DRUGBANK_API_KEY")


def fetch_smiles(drugbank_id: str) -> Optional[str]:
    """
    Fetches the SMILES string for a given DrugBank ID using PubChem via identifier mapping only.
    """
    typer.echo(f"-> Fetching SMILES via PubChem for {drugbank_id}")
    smiles = get_pubchem_smiles_from_drugbank(drugbank_id)
    if smiles:
        typer.secho(
            f"  [Success] Found SMILES via PubChem: {smiles[:30]}...",
            fg=typer.colors.GREEN,
        )
        return smiles
    else:
        typer.secho(
            f"  [Warning] No SMILES found via PubChem for {drugbank_id}.",
            fg=typer.colors.YELLOW,
        )
        return None


def fetch_protein_data(uniprot_id: str) -> tuple[str | None, str | None]:
    """
    Fetches the protein sequence and full name from the UniProt REST API.

    Args:
        uniprot_id: The UniProt identifier (e.g., 'P12821').

    Returns:
        A tuple containing (sequence, protein_name), or (None, None) if not found.
    """
    url = UNIPROT_API_TEMPLATE.format(uniprot_id)
    typer.echo(f"-> Fetching sequence from {url}")

    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()

        # Extract sequence and name using the paths from the user's jq filters
        sequence = data.get("sequence", {}).get("value")
        protein_name = (
            data.get("proteinDescription", {})
            .get("recommendedName", {})
            .get("fullName", {})
            .get("value")
        )

        if sequence and protein_name:
            typer.secho(
                f"  [Success] Found sequence for '{protein_name}'.",
                fg=typer.colors.GREEN,
            )
            return sequence, protein_name
        else:
            typer.secho(
                f"  [Warning] JSON response for {uniprot_id} is missing sequence or name.",
                fg=typer.colors.YELLOW,
            )
            return None, None

    except requests.exceptions.RequestException as e:
        typer.secho(
            f"  [Error] Failed to fetch data for {uniprot_id}: {e}", fg=typer.colors.RED
        )
        return None, None
    except requests.exceptions.JSONDecodeError:
        typer.secho(
            f"  [Error] Failed to decode JSON from UniProt for {uniprot_id}.",
            fg=typer.colors.RED,
        )
        return None, None


@app.command()
def yaml_files(
    input_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to the input YAML file containing IDs.",
    ),
    output_dir: Path = typer.Option(
        "data/affinities_config_files/",
        "--out",
        "-o",
        help="Directory to save the generated YAML files.",
        file_okay=False,
        dir_okay=True,
        writable=True,
    ),
    limit: int = typer.Option(
        None,
        "--limit",
        "-l",
        help="Limit the number of pairs to process.",
    ),
):
    """
    Generates drug-protein YAML files from a list of DrugBank and UniProt IDs.
    """
    typer.secho(f"Starting file generation from '{input_file}'", bold=True)

    # Create the output directory if it doesn't exist
    output_dir.mkdir(exist_ok=True)
    typer.echo(f"Outputting files to: '{output_dir.resolve()}'")

    with open(input_file, "r") as f:
        data = yaml.safe_load(f)

    if "pairs" not in data or not isinstance(data["pairs"], list):
        typer.secho(
            "Error: Input YAML must contain a top-level key 'pairs' which is a list.",
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=1)

    total_pairs = len(data["pairs"])
    for i, pair in enumerate(data["pairs"][:limit]):
        drug_name = pair.get("drug_name", "UnknownDrug")
        drugbank_id = pair.get("drugbank_id")
        uniprot_id = pair.get("uniprot_id")

        typer.echo("-" * 40)
        typer.secho(
            f"Processing Pair {i + 1}/{total_pairs}: {drug_name} ({drugbank_id}) | {uniprot_id}",
            bold=True,
        )

        if not drugbank_id or not uniprot_id:
            typer.secho(
                "  [Skipping] Missing DrugBank or UniProt ID in this entry.",
                fg=typer.colors.YELLOW,
            )
            continue

        # Fetch the data
        smiles = fetch_smiles(drugbank_id)
        sequence, protein_name = fetch_protein_data(uniprot_id)

        # Use placeholders if data is missing
        if not smiles:
            smiles = f"<MANUAL_SMILES_FOR_{drugbank_id}>"
        if not sequence:
            sequence = f"<MANUAL_SEQUENCE_FOR_{uniprot_id}>"
        if not protein_name:
            protein_name = f"<MANUAL_PROTEIN_NAME_FOR_{uniprot_id}>"

        # Prepare the YAML structure
        output_data = {
            "sequences": [
                {"protein": {"id": "A", "name": protein_name, "sequence": sequence}},
                {"ligand": {"id": "B", "name": drug_name, "smiles": smiles}},
            ],
            "properties": [{"affinity": {"binder": "B"}}],
        }

        # Create a clean filename
        safe_protein_name = protein_name.replace(" ", "_").replace("/", "_")
        output_filename = f"{drug_name}_{safe_protein_name}.yaml"
        output_path = output_dir / output_filename

        # Write the YAML file
        with open(output_path, "w") as f:
            yaml.dump(output_data, f, sort_keys=False, indent=2)

        typer.secho(
            f"✓ Successfully created '{output_path}'", fg=typer.colors.BRIGHT_GREEN
        )

    typer.echo("-" * 40)
    typer.secho("Generation complete!", bold=True)
