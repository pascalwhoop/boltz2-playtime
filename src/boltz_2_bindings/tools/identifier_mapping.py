from typing import Optional

import requests


def get_pubchem_smiles_from_drugbank(drugbank_id: str) -> Optional[str]:
    """
    Given a DrugBank ID (e.g., 'DB01118'), map it to a PubChem Compound ID using the NodeNormalization API,
    then fetch the SMILES string from PubChem.

    Args:
        drugbank_id: The DrugBank identifier (e.g., 'DB01118').

    Returns:
        The SMILES string if found, otherwise None.
    """
    # Step 1: Normalize DrugBank ID to PubChem Compound ID
    nn_url = (
        "https://nodenormalization-sri.renci.org/1.5/get_normalized_nodes"
        f"?curie=drugbank:{drugbank_id}&conflate=true&drug_chemical_conflate=false&description=false&individual_types=false"
    )
    try:
        nn_resp = requests.get(nn_url, timeout=10)
        nn_resp.raise_for_status()
        nn_data = nn_resp.json()
        eq_ids = nn_data.get(f"drugbank:{drugbank_id}", {}).get(
            "equivalent_identifiers", []
        )
        pubchem_cid = None
        for entry in eq_ids:
            identifier = entry.get("identifier", "")
            if identifier.startswith("PUBCHEM.COMPOUND:"):
                pubchem_cid = identifier.split(":", 1)[1]
                break
        if not pubchem_cid:
            return None
    except Exception:
        return None

    # Step 2: Fetch SMILES from PubChem
    pubchem_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{pubchem_cid}/property/smiles/json"
    try:
        pc_resp = requests.get(pubchem_url, timeout=10)
        pc_resp.raise_for_status()
        pc_data = pc_resp.json()
        smiles = (
            pc_data.get("PropertyTable", {}).get("Properties", [{}])[0].get("SMILES")
        )
        return smiles
    except Exception:
        return None
