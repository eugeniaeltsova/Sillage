# %% [markdown]
# # FragDB v4.6: Complete Data Exploration Guide
#
# This notebook provides a comprehensive exploration of the FragDB fragrance database sample.
#
# **Dataset contains 5 relational CSV files:**
# - `fragrances.csv` - 10 fragrances, 30 fields
# - `brands.csv` - 10 brands, 10 fields
# - `perfumers.csv` - 10 perfumers, 11 fields
# - `notes.csv` - 10 notes, 11 fields
# - `accords.csv` - 10 accords, 5 fields
#
# **Full database:** 125,698 fragrances, 7,500 brands, 2,881 perfumers, 1,826 notes, 92 accords at [fragdb.net](https://fragdb.net)

# %% [markdown]
# ## 1. Setup & Data Loading

# %%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import re
from collections import Counter

# Display settings
pd.set_option('display.max_columns', None)
pd.set_option('display.max_colwidth', 100)
plt.style.use('seaborn-v0_8-whitegrid')

# %%
# Load all 5 files (v4.6)
fragrances = pd.read_csv('/kaggle/input/fragdb-fragrance-database/fragrances.csv', sep='|')
brands = pd.read_csv('/kaggle/input/fragdb-fragrance-database/brands.csv', sep='|')
perfumers = pd.read_csv('/kaggle/input/fragdb-fragrance-database/perfumers.csv', sep='|')
notes = pd.read_csv('/kaggle/input/fragdb-fragrance-database/notes.csv', sep='|')
accords = pd.read_csv('/kaggle/input/fragdb-fragrance-database/accords.csv', sep='|')

print("Data loaded successfully!")
print(f"\nFragrances: {fragrances.shape[0]} rows x {fragrances.shape[1]} columns")
print(f"Brands: {brands.shape[0]} rows x {brands.shape[1]} columns")
print(f"Perfumers: {perfumers.shape[0]} rows x {perfumers.shape[1]} columns")
print(f"Notes: {notes.shape[0]} rows x {notes.shape[1]} columns")
print(f"Accords: {accords.shape[0]} rows x {accords.shape[1]} columns")
total_records = sum([len(df) for df in [fragrances, brands, perfumers, notes, accords]])
total_fields = sum([len(df.columns) for df in [fragrances, brands, perfumers, notes, accords]])
print(f"\nTotal: {total_records} records, {total_fields} fields")

# %% [markdown]
# ## 2. Data Overview

# %%
print("=" * 60)
print("FRAGRANCES.CSV - Column Overview (30 fields)")
print("=" * 60)
for i, col in enumerate(fragrances.columns, 1):
    non_null = fragrances[col].notna().sum()
    dtype = fragrances[col].dtype
    print(f"{i:2}. {col:<20} | {non_null}/{len(fragrances)} non-null | {dtype}")

# %%
print("=" * 60)
print("NOTES.CSV - Column Overview (11 fields) - NEW in v3.0")
print("=" * 60)
for i, col in enumerate(notes.columns, 1):
    non_null = notes[col].notna().sum()
    dtype = notes[col].dtype
    print(f"{i:2}. {col:<20} | {non_null}/{len(notes)} non-null | {dtype}")

# %%
print("=" * 60)
print("ACCORDS.CSV - Column Overview (5 fields) - NEW in v3.0")
print("=" * 60)
for i, col in enumerate(accords.columns, 1):
    non_null = accords[col].notna().sum()
    dtype = accords[col].dtype
    print(f"{i:2}. {col:<20} | {non_null}/{len(accords)} non-null | {dtype}")

# %% [markdown]
# ---
# # PART 1: NOTES.CSV (NEW in v3.0)
# ---

# %%
print("NOTES REFERENCE TABLE")
print("=" * 60)
print(notes[['id', 'name', 'latin_name', 'group', 'fragrance_count']].to_string())

# %%
# Notes by group
print("\nNotes by Group:")
print(notes['group'].value_counts().to_string())

# %%
# Visualize notes by fragrance count
fig, ax = plt.subplots(figsize=(12, 6))
notes_sorted = notes.sort_values('fragrance_count', ascending=True)
colors = plt.cm.Greens(np.linspace(0.3, 0.9, len(notes_sorted)))
ax.barh(notes_sorted['name'], notes_sorted['fragrance_count'], color=colors)
ax.set_xlabel('Number of Fragrances')
ax.set_title('Notes by Fragrance Count (Full Database)')
for i, (name, count) in enumerate(zip(notes_sorted['name'], notes_sorted['fragrance_count'])):
    ax.text(count + 200, i, f'{count:,}', va='center', fontsize=9)
plt.tight_layout()
plt.show()

# %%
# Show odor profiles
print("\nOdor Profiles:")
print("-" * 60)
for _, row in notes.iterrows():
    print(f"\n{row['name']}:")
    odor = str(row['odor_profile'])
    print(f"  {odor[:100]}..." if len(odor) > 100 else f"  {odor}")

# %% [markdown]
# ---
# # PART 2: ACCORDS.CSV (NEW in v3.0)
# ---

# %%
print("ACCORDS REFERENCE TABLE")
print("=" * 60)
print(accords.to_string())

# %%
# Visualize accords with their actual colors
fig, ax = plt.subplots(figsize=(12, 6))
accords_sorted = accords.sort_values('fragrance_count', ascending=True)

bars = ax.barh(accords_sorted['name'], accords_sorted['fragrance_count'],
               color=accords_sorted['bar_color'].tolist(), edgecolor='black')

ax.set_xlabel('Number of Fragrances')
ax.set_title('Accords by Fragrance Count (with actual display colors)')

for i, (name, count) in enumerate(zip(accords_sorted['name'], accords_sorted['fragrance_count'])):
    ax.text(count + 500, i, f'{count:,}', va='center', fontsize=9)

plt.tight_layout()
plt.show()

# %% [markdown]
# ---
# # PART 3: FRAGRANCES.CSV (30 Fields)
# ---

# %% [markdown]
# ## 3. Identity Fields

# %%
print("PID (Unique Fragrance Identifier)")
print("-" * 40)
print(f"Type: Integer")
print(f"Range: {fragrances['pid'].min()} - {fragrances['pid'].max()}")
print(f"Unique: {fragrances['pid'].nunique()} (100% unique)")
print(f"\nSample values:")
print(fragrances[['pid', 'name']].to_string(index=False))

# %%
print("BRAND (Format: brand_name;brand_id)")
print("-" * 40)
print("Raw values:")
print(fragrances['brand'].to_string(index=False))

# Parse brand field
fragrances['brand_name'] = fragrances['brand'].str.split(';').str[0]
fragrances['brand_id'] = fragrances['brand'].str.split(';').str[1]

print("\nParsed:")
print(fragrances[['brand', 'brand_name', 'brand_id']].to_string(index=False))

# %% [markdown]
# ## 4. Composition Fields (v3.0 Format)

# %% [markdown]
# ### 4.1 accords - NEW FORMAT in v3.0: id:percent

# %%
print("ACCORDS (v3.0 Format: id:percent;id:percent;...)")
print("-" * 40)
print("Raw example:")
print(fragrances['accords'].iloc[0])

# Parse accords v3.0 format
def parse_accords_v3(accords_str, accords_df):
    """Parse v3.0 accords format (id:percent) and join with accords reference"""
    if pd.isna(accords_str):
        return []
    result = []
    for item in accords_str.split(';'):
        parts = item.split(':')
        if len(parts) == 2:
            accord_id = parts[0]
            percent = int(parts[1]) if parts[1].isdigit() else 0
            # Look up accord details from reference table
            accord_info = accords_df[accords_df['id'] == accord_id]
            if not accord_info.empty:
                result.append({
                    'id': accord_id,
                    'name': accord_info['name'].iloc[0],
                    'percent': percent,
                    'bar_color': accord_info['bar_color'].iloc[0],
                    'font_color': accord_info['font_color'].iloc[0]
                })
    return result

# Example parsing
sample_accords = parse_accords_v3(fragrances['accords'].iloc[0], accords)
print(f"\nParsed accords for {fragrances['name'].iloc[0]}:")
for acc in sample_accords[:5]:
    print(f"  {acc['name']}: {acc['percent']}% (color: {acc['bar_color']})")

# %%
# Visualize accords for one fragrance with actual colors
sample_idx = 0
sample_name = fragrances['name'].iloc[sample_idx]
parsed_accords = parse_accords_v3(fragrances['accords'].iloc[sample_idx], accords)

if parsed_accords:
    acc_df = pd.DataFrame(parsed_accords).sort_values('percent', ascending=True)

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(acc_df['name'], acc_df['percent'],
                   color=acc_df['bar_color'].tolist(), edgecolor='black')
    ax.set_xlabel('Strength (%)')
    ax.set_title(f'Accords: {sample_name}')
    ax.set_xlim(0, 105)

    for bar, strength in zip(bars, acc_df['percent']):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2,
                f'{strength}%', va='center', fontsize=9)

    plt.tight_layout()
    plt.show()

# %% [markdown]
# ### 4.2 notes_pyramid - NEW FORMAT in v3.0 with opacity/weight

# %%
print("NOTES_PYRAMID (v3.0 Format: layer(name,id,url,opacity,weight;...))")
print("-" * 40)
print("Raw example (truncated):")
print(fragrances['notes_pyramid'].iloc[0][:200] + "...")

# Parse notes pyramid v3.0 format
def parse_notes_pyramid_v3(pyramid_str):
    """Parse v3.0 notes pyramid format with opacity and weight"""
    if pd.isna(pyramid_str):
        return {'top': [], 'middle': [], 'base': []}

    result = {'top': [], 'middle': [], 'base': []}

    # Find each layer
    for layer in ['top', 'middle', 'base']:
        pattern = rf'{layer}\(([^)]+)\)'
        match = re.search(pattern, pyramid_str, re.IGNORECASE)
        if match:
            notes_str = match.group(1)
            for note in notes_str.split(';'):
                parts = note.split(',')
                if parts[0]:
                    result[layer].append({
                        'name': parts[0],
                        'id': parts[1] if len(parts) > 1 else None,
                        'url': parts[2] if len(parts) > 2 else None,
                        'opacity': float(parts[3]) if len(parts) > 3 and parts[3] else None,
                        'weight': float(parts[4]) if len(parts) > 4 and parts[4] else None
                    })

    # Check for "notes(" which contains all notes without layers
    if not any(result.values()):
        pattern = r'notes\(([^)]+)\)'
        match = re.search(pattern, pyramid_str, re.IGNORECASE)
        if match:
            notes_str = match.group(1)
            for note in notes_str.split(';'):
                parts = note.split(',')
                if parts[0]:
                    result['top'].append({'name': parts[0], 'id': parts[1] if len(parts) > 1 else None})

    return result

# Example
sample_pyramid = parse_notes_pyramid_v3(fragrances['notes_pyramid'].iloc[0])
print(f"\nParsed pyramid for {fragrances['name'].iloc[0]}:")
for layer, layer_notes in sample_pyramid.items():
    if layer_notes:
        print(f"  {layer.upper()}:")
        for n in layer_notes[:3]:
            opacity_str = f", opacity={n['opacity']}" if n.get('opacity') else ""
            weight_str = f", weight={n['weight']}" if n.get('weight') else ""
            print(f"    - {n['name']} (id={n['id']}{opacity_str}{weight_str})")

# %% [markdown]
# ## 5. Voting Fields (v3.0 Format: category:votes:percent)

# %%
print("v3.0 VOTING FORMAT: category:votes:percent")
print("=" * 60)
print("\nExample longevity field:")
print(fragrances['longevity'].iloc[0])

# Parse v3.0 voting format
def parse_votes_v3(votes_str):
    """Parse v3.0 voting format (category:votes:percent)"""
    if pd.isna(votes_str):
        return {}
    result = {}
    for item in votes_str.split(';'):
        parts = item.split(':')
        if len(parts) >= 3:
            result[parts[0]] = {
                'votes': int(parts[1]) if parts[1].isdigit() else 0,
                'percent': float(parts[2]) if parts[2].replace('.','').isdigit() else 0
            }
    return result

# Example parsing
sample_longevity = parse_votes_v3(fragrances['longevity'].iloc[0])
print(f"\nParsed longevity for {fragrances['name'].iloc[0]}:")
for cat, data in sample_longevity.items():
    print(f"  {cat}: {data['votes']:,} votes ({data['percent']}%)")

# %%
# Calculate weighted longevity score
def longevity_score(lon_str):
    parsed = parse_votes_v3(lon_str)
    weights = {'very_weak': 1, 'weak': 2, 'moderate': 3, 'long_lasting': 4, 'eternal': 5}
    total_votes = sum(d['votes'] for d in parsed.values())
    if total_votes == 0:
        return 0
    weighted_sum = sum(parsed.get(k, {'votes': 0})['votes'] * v for k, v in weights.items())
    return weighted_sum / total_votes

fragrances['longevity_score'] = fragrances['longevity'].apply(longevity_score)
print("Longevity Score (1-5):")
print(fragrances[['name', 'longevity_score']].sort_values('longevity_score', ascending=False).to_string(index=False))

# %%
# Calculate weighted sillage score
def sillage_score(sil_str):
    parsed = parse_votes_v3(sil_str)
    weights = {'intimate': 1, 'moderate': 2, 'strong': 3, 'enormous': 4}
    total_votes = sum(d['votes'] for d in parsed.values())
    if total_votes == 0:
        return 0
    weighted_sum = sum(parsed.get(k, {'votes': 0})['votes'] * v for k, v in weights.items())
    return weighted_sum / total_votes

fragrances['sillage_score'] = fragrances['sillage'].apply(sillage_score)
print("Sillage Score (1-4):")
print(fragrances[['name', 'sillage_score']].sort_values('sillage_score', ascending=False).to_string(index=False))

# %%
# Parse rating (format: average;votes)
fragrances[['rating_avg', 'rating_votes']] = fragrances['rating'].str.split(';', expand=True)
fragrances['rating_avg'] = pd.to_numeric(fragrances['rating_avg'], errors='coerce')
fragrances['rating_votes'] = pd.to_numeric(fragrances['rating_votes'], errors='coerce')

# Visualize Longevity vs Sillage
fig, ax = plt.subplots(figsize=(10, 8))

scatter = ax.scatter(fragrances['longevity_score'], fragrances['sillage_score'],
                     s=fragrances['rating_votes']/50, alpha=0.7, c=fragrances['rating_avg'],
                     cmap='RdYlGn', edgecolors='black')

for idx, row in fragrances.iterrows():
    ax.annotate(row['name'], (row['longevity_score'], row['sillage_score']),
                xytext=(5, 5), textcoords='offset points', fontsize=8)

ax.set_xlabel('Longevity Score (1-5)')
ax.set_ylabel('Sillage Score (1-4)')
ax.set_title('Longevity vs Sillage (bubble size = votes, color = rating)')
plt.colorbar(scatter, label='Rating')
plt.tight_layout()
plt.show()

# %% [markdown]
# ## 6. New Fields in v3.0

# %% [markdown]
# ### 6.1 reviews_count - Total Reviews

# %%
print("REVIEWS_COUNT (NEW in v3.0)")
print("-" * 40)
print(fragrances[['name', 'reviews_count']].sort_values('reviews_count', ascending=False).to_string(index=False))

# %% [markdown]
# ---
# # PART 4: BRANDS.CSV (10 Fields)
# ---

# %%
print("=" * 60)
print("BRANDS TABLE")
print("=" * 60)
print(brands[['id', 'name', 'country', 'main_activity', 'brand_count']].to_string())

# %%
# Visualize brands
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# By country
ax1 = axes[0]
country_counts = brands['country'].value_counts()
ax1.pie(country_counts.values, labels=country_counts.index, autopct='%1.0f%%', startangle=90)
ax1.set_title('Brands by Country')

# By fragrance count
ax2 = axes[1]
brands_sorted = brands.sort_values('brand_count', ascending=True)
ax2.barh(brands_sorted['name'], brands_sorted['brand_count'], color='steelblue')
ax2.set_xlabel('Number of Fragrances')
ax2.set_title('Brands by Fragrance Count')

plt.tight_layout()
plt.show()

# %% [markdown]
# ---
# # PART 5: PERFUMERS.CSV (11 Fields)
# ---

# %%
print("=" * 60)
print("PERFUMERS TABLE")
print("=" * 60)
print(perfumers[['id', 'name', 'status', 'company', 'perfumes_count']].to_string())

# %%
# Top perfumers by fragrance count
fig, ax = plt.subplots(figsize=(12, 6))
perf_sorted = perfumers.sort_values('perfumes_count', ascending=True)
colors = plt.cm.viridis(np.linspace(0.2, 0.8, len(perf_sorted)))
ax.barh(perf_sorted['name'], perf_sorted['perfumes_count'], color=colors)
ax.set_xlabel('Number of Fragrances Created')
ax.set_title('Perfumers by Fragrance Count')
for i, (name, count) in enumerate(zip(perf_sorted['name'], perf_sorted['perfumes_count'])):
    ax.text(count + 5, i, str(count), va='center', fontsize=9)
plt.tight_layout()
plt.show()

# %% [markdown]
# ---
# # PART 6: JOINING TABLES
# ---

# %%
# Join fragrances with brands
df = fragrances.merge(brands, left_on='brand_id', right_on='id', suffixes=('', '_brand'))

print("Joined fragrances + brands:")
print(df[['name', 'name_brand', 'country', 'year', 'rating_avg']].to_string(index=False))

# %%
# Join accords with fragrance accords
print("\nJoining fragrance accords with accords reference:")
print("-" * 60)

for idx, row in fragrances.head(3).iterrows():
    print(f"\n{row['name']}:")
    parsed = parse_accords_v3(row['accords'], accords)
    for acc in parsed[:3]:
        print(f"  - {acc['name']}: {acc['percent']}% (color: {acc['bar_color']})")

# %% [markdown]
# ---
# # PART 7: SUMMARY
# ---

# %%
print("=" * 60)
print("FRAGDB v4.6 DATASET SUMMARY")
print("=" * 60)
print(f"""
SAMPLE DATASET (5 files, 67 fields):
  - Fragrances: {len(fragrances)} records, {len(fragrances.columns)} fields
  - Brands: {len(brands)} records, {len(brands.columns)} fields
  - Perfumers: {len(perfumers)} records, {len(perfumers.columns)} fields
  - Notes: {len(notes)} records, {len(notes.columns)} fields (NEW)
  - Accords: {len(accords)} records, {len(accords.columns)} fields (NEW)

KEY INSIGHTS:
  - Average rating: {fragrances['rating_avg'].mean():.2f}/5
  - Total rating votes: {fragrances['rating_votes'].sum():,.0f}
  - Year range: {fragrances['year'].min()} - {fragrances['year'].max()}
  - Countries represented: {brands['country'].nunique()}

KEY FEATURES:
  - notes.csv: Latin names, odor profiles, images
  - accords.csv: Display colors (bar_color, font_color)
  - Voting format: category:votes:percent
  - Accords format: id:percent (join with accords.csv)
  - Notes pyramid: name,id,url,opacity,weight

FULL DATABASE (fragdb.net):
  - 125,698 fragrances
  - 7,500 brands
  - 2,881 perfumers
  - 1,826 notes
  - 92 accords
  - Total: 137,997 records
""")

# %% [markdown]
# ## Links
#
# - **Full Database**: [fragdb.net](https://fragdb.net)
# - **GitHub**: [github.com/FragDB/fragrance-database](https://github.com/FragDB/fragrance-database)
# - **Hugging Face**: [huggingface.co/datasets/FragDBnet/fragrance-database](https://huggingface.co/datasets/FragDBnet/fragrance-database)
# - **Documentation**: [Data Dictionary](https://github.com/FragDB/fragrance-database/blob/main/DATA_DICTIONARY.md)
