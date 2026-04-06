# FragDB - Fragrantica Fragrance Database

This is a **FREE SAMPLE** of FragDB v4.6, the largest structured fragrance database available. Perfect for building recommendation systems, market analysis, and fragrance discovery apps.

## What's Included (Sample v4.6)

| File | Records | Fields | Description |
|------|---------|--------|-------------|
| `fragrances.csv` | 10 | 30 | Iconic fragrances with full data |
| `brands.csv` | 10 | 10 | Brand profiles |
| `perfumers.csv` | 10 | 11 | Perfumer profiles |
| `notes.csv` | 10 | 11 | Fragrance notes (NEW) |
| `accords.csv` | 10 | 5 | Accords with colors (NEW) |

## Full Database Statistics

| | Sample | Full Database |
|---|--------|---------------|
| Fragrances | 10 | **125,698** |
| Brands | 10 | **7,500** |
| Perfumers | 10 | **2,881** |
| Notes | 10 | **1,826** |
| Accords | 10 | **92** |
| Total Records | 50 | **137,997** |
| Data Fields | 67 | 67 |

## What's New in v4.6

- **Updated data**: 125,698 fragrances, 7,500 brands, 2,881 perfumers, 1,826 notes
- **Field**: `video_url` — YouTube video URLs for fragrances
- **67 data fields** across 5 interconnected CSV files

## About the Files

### fragrances.csv (10 records, 30 fields)
Sample of 10 iconic fragrances. Each record contains:
- **Identity**: pid, url, name, brand, year, gender, collection
- **Composition**: accords (id:percent), notes_pyramid (with opacity/weight), perfumers
- **Ratings**: rating, reviews_count, appreciation, longevity, sillage, price_value
- **Voting**: All voting fields use `category:votes:percent` format
- **AI**: pros_cons (What People Say)
- **Related**: also_like, reminds_of (pid:likes:dislikes)
- **Media**: main_photo, info_card, user_photos, video_url (NEW)

### brands.csv (10 records, 10 fields)
Brand profiles:
- **Identity**: id, name, url, logo_url
- **Details**: country, main_activity, website, parent_company
- **Content**: description, brand_count

### perfumers.csv (10 records, 11 fields)
Perfumer (nose) profiles:
- **Identity**: id, name, url, photo_url
- **Professional**: status, company, also_worked, education, web
- **Content**: perfumes_count, biography

### notes.csv (10 records, 11 fields) — NEW in v3.0
Fragrance note reference:
- **Identity**: id, name, url
- **Details**: latin_name, other_names, group, odor_profile
- **Media**: main_icon, alt_icons, background
- **Stats**: fragrance_count

### accords.csv (10 records, 5 fields) — NEW in v3.0
Accord reference with display colors:
- **Identity**: id, name
- **Display**: bar_color (hex), font_color (hex)
- **Stats**: fragrance_count

## Quick Start

```python
import pandas as pd

# Load all 5 files
fragrances = pd.read_csv('fragrances.csv', sep='|')
brands = pd.read_csv('brands.csv', sep='|')
perfumers = pd.read_csv('perfumers.csv', sep='|')
notes = pd.read_csv('notes.csv', sep='|')
accords = pd.read_csv('accords.csv', sep='|')

# Join fragrances with brands
fragrances['brand_id'] = fragrances['brand'].str.split(';').str[1]
merged = fragrances.merge(brands, left_on='brand_id', right_on='id', suffixes=('', '_brand'))

# Parse voting field (v3.0 format)
def parse_votes(field):
    if not field: return {}
    return {p.split(':')[0]: {'votes': int(p.split(':')[1]), 'pct': float(p.split(':')[2])}
            for p in field.split(';') if ':' in p}

longevity = parse_votes(fragrances.iloc[0]['longevity'])
print(longevity)
```

## Use Cases

- **Recommendation Systems** — Build "if you like X, try Y" engines
- **Market Analysis** — Track industry trends, brand portfolios
- **E-commerce** — Enrich product catalogs with detailed data
- **Mobile Apps** — Create fragrance discovery experiences
- **Data Visualization** — Use accord colors for visual displays
- **Research** — Analyze scent composition patterns

## File Format

- **Format**: CSV (pipe `|` delimited)
- **Encoding**: UTF-8
- **Quote Character**: `"` (double quote)

## Get the Full Database

This sample demonstrates the data quality and structure. The full FragDB database with **137,997 records** is available at:

### [fragdb.net](https://fragdb.net)

## License

This sample is provided under **CC-BY-NC-4.0** (Attribution-NonCommercial).
- Free for research and personal projects
- Commercial use requires full database license

## Links

- **Full Database**: [fragdb.net](https://fragdb.net)
- **GitHub**: [github.com/FragDB/fragrance-database](https://github.com/FragDB/fragrance-database)
- **Hugging Face**: [huggingface.co/datasets/FragDBnet/fragrance-database](https://huggingface.co/datasets/FragDBnet/fragrance-database)
- **Documentation**: [Data Dictionary](https://github.com/FragDB/fragrance-database/blob/main/DATA_DICTIONARY.md)

---

*Last updated: March 2026 (v4.6)*
