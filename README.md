# Sillage — AI Fragrance Discovery

> *Sillage* (n.) — the trail a fragrance leaves in the air. A measure of how far a perfume carries, and how long it lingers.

An AI-powered fragrance advisor that helps you find perfumes that match your taste through natural conversation. Powered by GPT-4.1, semantic vector search across 24,000+ fragrances, and a curated Fragrantica dataset.

![Starting page](ui/public/Screenshots/starting_page.png)

---

## Features

- **Conversational discovery** — describe a mood, an occasion, or a feeling; the agent extracts your preferences through natural dialogue
- **Semantic search** — vector embeddings capture scent character beyond keyword matching
- **Reference-based fusion** — "find me something like Dior Sauvage but darker" uses weighted vector fusion (0.6 × description + 0.4 × reference)
- **Advanced filtering** — gender, year range, brand, perfumer, specific notes (include and exclude)
- **Dark horse recommendations** — one niche candidate per search with high semantic fit but low commercial visibility
- **Fragrance comparison** — side-by-side breakdown of two perfumes
- **Multi-language** — responds in the user's language

![Fragrance result cards](ui/public/Screenshots/fragrance_cards.png)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 19, Axios |
| Backend | FastAPI, Python 3.11+ |
| AI / LLM | Azure OpenAI GPT-4.1 (agentic tool use) |
| Embeddings | Azure OpenAI `text-embedding-3-small` |
| Vector DB | Qdrant Cloud (ANN search + payload filtering) |
| Fuzzy matching | RapidFuzz (token sort ratio, ≥80% threshold) |
| Data | FragDB v4.6 — 24,000+ Fragrantica fragrances |

---

## Architecture

```
User message
     │
     ▼
React frontend  ──POST /chat──►  FastAPI backend
                                      │
                              Agentic loop (GPT-4.1)
                              decides which tool to call
                                      │
                    ┌─────────────────┼──────────────────┐
                    ▼                 ▼                   ▼
           search_perfumes     lookup_perfume     compare_perfumes
                    │
          Build query vector
          (description + reference fusion)
                    │
          Qdrant ANN search + payload filters
                    │
          Re-rank by rating score
          Extract dark horse candidate
                    │
                    └──► Top 5 results ──► GPT-4.1 ──► Response
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- An [Azure OpenAI](https://azure.microsoft.com/en-us/products/ai-services/openai-service) resource with:
  - A `gpt-4.1` deployment
  - A `text-embedding-3-small` deployment
- A [Qdrant Cloud](https://cloud.qdrant.io/) cluster with a pre-populated `perfumes` collection

### Backend

```bash
# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables (see below)
cp .env.example .env
# Edit .env with your credentials

# Run the API server
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

### Frontend

```bash
cd ui
cp .env.example .env   # already configured for localhost:8000
npm install
npm start
```

The app will open at `http://localhost:3000`.

---

## Environment Variables

Create a `.env` file at the project root:

```env
AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com/
AZURE_OPENAI_KEY=<your-api-key>
QDRANT_URL=https://<your-cluster>.cloud.qdrant.io
QDRANT_API_KEY=<your-qdrant-api-key>
```

The frontend needs only one variable (already set in `ui/.env.example`):

```env
REACT_APP_API_URL=http://localhost:8000
```

---

## How It Works

### Search Pipeline

1. **Preference extraction** — GPT-4.1 extracts scent descriptors, gender, year range, brand preferences, and any reference perfumes from the conversation
2. **Vector construction** — the scent description is embedded; if a reference perfume is provided, its stored vector is retrieved and fused: `0.6 × description + 0.4 × reference`
3. **ANN search** — Qdrant returns the top 200 nearest neighbours, filtered by any hard constraints (gender, year, notes, brand)
4. **Re-ranking** — candidates are scored by `rating × log10(review_count + 1)` to balance quality with recognition
5. **Dark horse extraction** — a niche candidate (high cosine similarity, <200 reviews) is pulled and presented last

### Multi-reference fusion

When the user references more than one perfume, each combination of (description + reference) is searched independently for top 50 results. The sets are merged, deduplicated, and re-ranked by frequency of appearance across searches, then by rating score.

### Agentic loop

The backend runs an agentic loop (max 10 iterations). GPT-4.1 autonomously decides whether to search, look up a specific perfume, or compare two candidates — calling tools until it has enough data to compose a final response.

---

## Screenshots

| | |
|---|---|
| ![Comparison](ui/public/Screenshots/Comparing_fragrances.png) | ![Negative filtering](ui/public/Screenshots/negative_filtering.png) |
| Side-by-side fragrance comparison | Exclusion filters — avoid specific notes or brands |
| ![German](ui/public/Screenshots/Deutsch.png) | ![Italian](ui/public/Screenshots/Italienisch.png) |
| Multi-language: German | Multi-language: Italian |

---

## Data

Fragrance data sourced from **FragDB v4.6**, a structured dataset derived from [Fragrantica](https://www.fragrantica.com). The full archive (~125k entries) is excluded from this repository.

---

## Note on deployment

This project requires a pre-populated Qdrant collection with perfume vectors. The ETL pipeline (embedding generation, data cleaning, upload) is not included in this repository. The application is designed to run against an existing cloud-hosted collection.
