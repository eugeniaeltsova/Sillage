from app.search import search_perfumes, vector_search
from app.utils import qdrant_client, openai_client, find_perfume_by_name, COLLECTION_NAME
from qdrant_client.models import Filter, FieldCondition, MatchValue
import numpy as np

# ── Perfume name list (populated at startup by main.py) ───────────────────────
perfume_names: list[str] = []
perfume_name_to_id: dict[str, int] = {}

# ── Lookup perfume by name ────────────────────────────────────────────────────
def lookup_perfume(name: str) -> dict | None:
    matched_name = find_perfume_by_name(name, perfume_names)
    print(f"Matched name: '{matched_name}'")
    print(f"In dict: {matched_name in perfume_name_to_id}")

    # Check similar keys in dict
    #similar = [k for k in perfume_name_to_id.keys() if "terre" in k.lower()]

    #Debug — remove after fixing
    #print(f"Similar keys in dict: {similar}")
    
    if not matched_name:
        return None

    point_id = perfume_name_to_id.get(matched_name)

    #Debug — remove after fixing
    #print(f"Point ID: {point_id}")

    if point_id is None:
        return None

    results = qdrant_client.retrieve(
        collection_name=COLLECTION_NAME,
        ids=[point_id],
        with_payload=True,
        with_vectors=False
    )
    if not results:
        return None

    return {
        "id": point_id,
        "payload": results[0].payload
    }

# ── Search perfumes (called by agent) ─────────────────────────────────────────
def tool_search_perfumes(
    description: str,
    referenced_perfume_names: list[str] = None,
    gender: str = None,
    year_from: int = None,
    year_to: int = None,
    brand: str = None,
    perfumer: str = None,
    exclude_brands: list[str] = None,
    exclude_perfumers: list[str] = None,
    exclude_notes: list[str] = None,
    include_notes: list[str] = None,
    top_n: int = 4
) -> dict:

    # Look up each reference perfume → get notes_combined and id
    reference_notes = []
    reference_ids = []

    if referenced_perfume_names:
        for name in referenced_perfume_names:
            result = lookup_perfume(name)
            if result:
                reference_notes.append(
                    result["payload"].get("notes_combined", "")
                )
                reference_ids.append(result["id"])

    # Call core search
    return search_perfumes(
        description=description,
        reference_notes=reference_notes if reference_notes else None,
        reference_ids=reference_ids if reference_ids else None,
        gender=gender,
        year_from=year_from,
        year_to=year_to,
        brand=brand,
        perfumer=perfumer,
        exclude_brands=exclude_brands,
        exclude_perfumers=exclude_perfumers,
        exclude_notes=exclude_notes,
        include_notes=include_notes,
        top_n=top_n
    )

# ── Compare two perfumes ──────────────────────────────────────────────────────
def tool_compare_perfumes(name_a: str, name_b: str) -> dict:
    result_a = lookup_perfume(name_a)
    result_b = lookup_perfume(name_b)

    if not result_a and not result_b:
        return {"error": f"Neither '{name_a}' nor '{name_b}' were found in the database."}
    if not result_a:
        return {"error": f"'{name_a}' was not found in the database."}
    if not result_b:
        return {"error": f"'{name_b}' was not found in the database."}

    return {
        "perfume_a": result_a["payload"],
        "perfume_b": result_b["payload"]
    }

# ── Get perfume details ───────────────────────────────────────────────────────
def tool_get_perfume_details(name: str) -> dict:
    result = lookup_perfume(name)
    if not result:
        return {"error": f"'{name}' was not found in the database."}
    return result["payload"]