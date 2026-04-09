import numpy as np
from qdrant_client.models import Filter, FieldCondition, MatchValue, Range
from qdrant_client.models import QueryRequest   
from app.utils import get_embedding, qdrant_client, COLLECTION_NAME

# ── Vector fusion ─────────────────────────────────────────────────────────────
def fuse_vectors(vec_a: list, vec_b: list, weight_a: float = 0.6) -> list:
    arr_a = np.array(vec_a)
    arr_b = np.array(vec_b)
    fused = weight_a * arr_a + (1 - weight_a) * arr_b
    # Normalise to unit length for cosine similarity
    fused = fused / np.linalg.norm(fused)
    return fused.tolist()

# ── Build Qdrant filter ───────────────────────────────────────────────────────
def build_filter(
    gender: str = None,
    year_from: int = None,
    year_to: int = None,
    brand: str = None,
    perfumer: str = None,
    exclude_brands: list[str] = None,
    exclude_perfumers: list[str] = None,
) -> Filter | None:
    conditions = []
    must_not_conditions = []

    if gender:
        conditions.append(
            FieldCondition(key="Gender", match=MatchValue(value=gender))
        )
    if brand:
        conditions.append(
            FieldCondition(key="Brand", match=MatchValue(value=brand))
        )
    if perfumer:
        conditions.append(
            FieldCondition(key="Perfumer1", match=MatchValue(value=perfumer))
        )
    if year_from or year_to:
        conditions.append(
            FieldCondition(
                key="Year",
                range=Range(
                    gte=year_from if year_from else 0,
                    lte=year_to if year_to else 9999
                )
            )
        )

      # ── Negative filters ─────────────────────────────────────────────
    if exclude_brands:
        for b in exclude_brands:
            must_not_conditions.append(
                FieldCondition(key="Brand", match=MatchValue(value=b))
            )

    if exclude_perfumers:
        for p in exclude_perfumers:
            must_not_conditions.append(
                FieldCondition(key="Perfumer1", match=MatchValue(value=p))
            )

    if not conditions and not must_not_conditions:
        return None

    return Filter(
        must=conditions if conditions else None,
        must_not=must_not_conditions if must_not_conditions else None
    )

# ── Re-rank by rating score ───────────────────────────────────────────────────
def rerank_by_score(candidates: list) -> list:
    import math
    for c in candidates:
        rating = c["payload"].get("Rating Value", 0)
        count = c["payload"].get("Rating Count", 0)
        c["ranking_score"] = rating * math.log10(count + 1)
    return sorted(candidates, key=lambda x: x["ranking_score"], reverse=True)

# ── Identify dark horse ───────────────────────────────────────────────────────
def extract_dark_horse(candidates: list) -> tuple[dict, list]:
    # Dark horse: high ANN similarity score but low rating count
    dark_horse_pool = [
        c for c in candidates
        if c["payload"].get("Rating Count", 0) < 200
    ]
    if not dark_horse_pool:
        return None, candidates

    # Pick the one with highest vector similarity score among niche candidates
    dark_horse = max(dark_horse_pool, key=lambda x: x.get("score", 0))
    remaining = [c for c in candidates if c != dark_horse]
    return dark_horse, remaining

# ── Single vector search ──────────────────────────────────────────────────────
def vector_search(
    query_vector: list,
    qdrant_filter: Filter = None,
    limit: int = 200
) -> list:
    results = qdrant_client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        query_filter=qdrant_filter,
        limit=limit,
        with_payload=True
    ).points

    return [
        {
            "id": r.id,
            "score": r.score,
            "payload": r.payload
        }
        for r in results
    ]


# ── Main search function ──────────────────────────────────────────────────────
def search_perfumes(
    description: str,
    reference_notes: list[str] = None,   # notes_combined for each reference perfume
    reference_ids: list[str] = None,  
    gender: str = None,
    year_from: int = None,
    year_to: int = None,
    brand: str = None,
    perfumer: str = None,
    exclude_brands: list[str] = None,       
    exclude_perfumers: list[str] = None,    
    exclude_notes: list[str] = None,
    include_notes: list[str] = None,
    top_n: int = 5
) -> dict:

    # Build filter
    qdrant_filter = build_filter(
        gender=gender,
        year_from=year_from,
        year_to=year_to,
        brand=brand,
        perfumer=perfumer,
        exclude_brands=exclude_brands,
        exclude_perfumers=exclude_perfumers,
    )

    # Embed description
    vec_a = get_embedding(description)

    # Search
    if not reference_notes:
        # No reference perfumes — description vector only
        candidates = vector_search(vec_a, qdrant_filter, limit=200)
    else:
        # Multiple reference perfumes — search separately and merge
        all_results = {}

        for ref_notes in reference_notes:
            vec_b = get_embedding(ref_notes)
            fused = fuse_vectors(vec_a, vec_b, weight_a=0.6)
            results = vector_search(fused, qdrant_filter, limit=50)

            for r in results:
                pid = r["id"]
                if pid not in all_results:
                    all_results[pid] = r
                    all_results[pid]["appearance_count"] = 1
                else:
                    all_results[pid]["appearance_count"] += 1

        # Sort by frequency of appearance, then by ANN score
        candidates = sorted(
            all_results.values(),
            key=lambda x: (x["appearance_count"], x["score"]),
            reverse=True
        )
       
    # ── Remove reference perfumes from results ────────────────────────────────
    if reference_ids:
        candidates = [
            c for c in candidates
            if c["id"] not in reference_ids
        ]

    # ── Exclude notes (substring match against notes_combined) ────────────────
    if exclude_notes:
        normalised_excludes = [n.lower() for n in exclude_notes]
        candidates = [
            c for c in candidates
            if not any(
                note in c["payload"].get("notes_combined", "").lower()
                for note in normalised_excludes
            )
        ]

    # ── Include notes (all specified notes must be present) ───────────────────
    if include_notes:
        normalised_includes = [n.lower() for n in include_notes]
        candidates = [
            c for c in candidates
            if all(
                note in c["payload"].get("notes_combined", "").lower()
                for note in normalised_includes
            )
        ]

    # Extract dark horse before re-ranking
    dark_horse, candidates = extract_dark_horse(candidates)

    # Re-rank by rating score
    ranked = rerank_by_score(candidates)

    # Take top N — reserve last slot for dark horse
    top_results = ranked[:top_n - 1 if dark_horse else top_n]

    # Append dark horse at the end
    if dark_horse:
        top_results.append(dark_horse)

    return {
        "results": top_results,
        "dark_horse": dark_horse is not None
    }