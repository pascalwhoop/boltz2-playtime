# Boltz-2 Experiment

This project uses the [Boltz](https://github.com/jwohlwend/boltz) biomolecular interaction models to predict binding affinities and other properties for protein-ligand pairs.

## Get started

> ❗Requires `uv`. Please get that first.

```bash
uv sync
source .venv/bin/activate
b2aff

# generates YAML files for all pairs in data/inputs_generate.yaml
b2aff generate yaml_files data/inputs_generate.yaml 
```
## How This Project Uses Boltz

- **Boltz** is a state-of-the-art deep learning model for biomolecular structure and binding affinity prediction, released under the MIT license. See the [Boltz GitHub repository](https://github.com/jwohlwend/boltz) for more details, installation, and citation instructions.
- This project prepares input YAML files describing protein-ligand pairs in `data/affinities_config_files/`.
- The Boltz model is run on these files to generate predictions for binding affinity and related properties.

## Running Predictions

To run predictions on all the affinity configuration files in this project, use the following command:

```sh
boltz predict data/affinities_config_files/ --use_msa_server
```

- This command will process all YAML files in the `data/affinities_config_files/` directory.
- The `--use_msa_server` flag enables automatic MSA (multiple sequence alignment) generation for protein sequences, which is recommended for best results.
- The output will include predictions such as `affinity_pred_value` (predicted binding affinity as log(IC50)) and `affinity_probability_binary` (probability the ligand is a binder).

## Input Format

Each YAML file in `data/affinities_config_files/` describes a protein-ligand pair, including:
- Protein sequence and metadata
- Ligand name and SMILES string
- Properties to predict (e.g., affinity)

See the example files in that directory for the required format.

## References

- [Boltz GitHub repository](https://github.com/jwohlwend/boltz)
- For more information on input formats and prediction options, see the [Boltz prediction instructions](https://github.com/jwohlwend/boltz#inference).
