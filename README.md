# Spotify Decoded

**5.5 years of personal Spotify data, analyzed.**

I requested my full streaming history from Spotify and turned it into an end-to-end data science project — exploratory analysis, machine learning, a session-based recommender system, and an interactive dashboard. Every insight in this project comes from my own listening data, which makes it something no template or tutorial dataset could replicate.

If you want to do the same, you can request your own extended streaming history from Spotify at **Settings > Security and Privacy > Download your data**. Select "Extended streaming history" and Spotify will email it to you within 30 days.

---

## What this project covers

- **Exploratory data analysis** across 80,000+ plays, 1,750 artists, and 3 countries from October 2020 to April 2026
- **Skip prediction** using a Random Forest classifier with 15 behavioural features, achieving AUC 0.74 on a temporal holdout set
- **Listener persona clustering** using KMeans on artist-level engagement features, producing 3 interpretable clusters
- **Track recommender** built from session co-occurrence patterns across 5,485 listening sessions using Dice coefficient normalization
- **Interactive Streamlit dashboard** with dynamic year filtering, personal narrative, and a live track recommender

---

## Project structure

```
spotify-decoded/
├── data/
│   ├── raw/               # Original Spotify JSON files (not in repo)
│   └── processed/         # Cleaned CSV used by the dashboard
├── notebooks/
│   ├── 01_eda.ipynb           # Exploratory data analysis
│   ├── 02_deep_analysis.ipynb # Sessions, streaks, engagement
│   ├── 03_ml_models.ipynb     # Skip predictor + clustering
│   └── 04_recommender.ipynb   # Session co-occurrence recommender
├── src/
│   └── spotify_parser.py  # Data loading and cleaning pipeline
├── dashboard/
│   └── app.py             # Streamlit dashboard
├── models/                # Saved model files (not in repo)
├── outputs/               # Chart exports from notebooks
└── requirements.txt
```

---

## Tech stack

| Category | Tools |
|---|---|
| Data processing | Python, pandas, numpy |
| Visualisation | matplotlib, seaborn, plotly |
| Machine learning | scikit-learn (Random Forest, KMeans) |
| Dashboard | Streamlit |
| Environment | Jupyter, conda |

---

## Key findings

- NCT DREAM account for 503 hours — nearly 15% of all listening time across 5.5 years
- *Teddy Bear* has 1,112 plays spanning March 2022 to January 2026, across two countries
- Skip rate rose from 0% (unrecorded in older exports) to 35.5% in 2022 onwards, peaking alongside the highest ever listening volume in 2025
- Late night listening (midnight to 5am) grew from 54 plays in 2021 to 6,028 in 2025
- The skip predictor achieves AUC 0.74 using only behavioural context — no audio features required
- Three listener personas emerged from clustering: core K-pop listening, Tamil and Telugu browsing, and NCT DREAM as a category of one

---

## Recommender system note

Three approaches to content-based filtering were attempted before the final design:

1. **Spotify Audio Features API** — deprecated for new developer accounts in November 2024
2. **Kaggle dataset (1.2M tracks)** — matched only 37% of the catalog due to poor K-pop and South Indian music coverage
3. **Last.fm tags** — matched 11% for the same reason

The final recommender is built entirely from session co-occurrence patterns. Tracks that consistently appeared in the same listening sessions are scored using Dice coefficient normalization, with a sequential play bonus for back-to-back listens. This approach is more personal than any external database could have produced.

---

## Running locally

```bash
# Clone the repo
git clone https://github.com/heyybaragi/spotify-decoded.git
cd spotify-decoded

# Install dependencies
pip install -r requirements.txt

# Run the dashboard
streamlit run dashboard/app.py
```

The dashboard loads from `data/processed/tracks_clean.csv`. If you want to run the notebooks, place your own Spotify JSON files in `data/raw/` and run `src/spotify_parser.py` first.

---

## Live demo

[View the dashboard](https://spotify-decoded-heyybaragi.streamlit.app/) ← update this after deployment

---

*Built by Sneha — [@heyybaragi](https://github.com/heyybaragi)*
