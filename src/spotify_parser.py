"""
spotify_parser.py
─────────────────
Loads and cleans all Spotify Extended Streaming History JSON files
into two analysis-ready DataFrames:
  - df_tracks   : music plays (80 000+ rows)
  - df_podcasts : podcast plays

Usage
-----
from spotify_parser import load_all

df_tracks, df_podcasts = load_all("data/")   # pass folder containing JSON files
"""

import json
import glob
from pathlib import Path

import pandas as pd
import numpy as np


# ── 1. LOAD ──────────────────────────────────────────────────────────────────

def load_all(folder: str = ".") -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load every Streaming_History_Audio_*.json in `folder`,
    merge into one DataFrame, clean it, and return
    (df_tracks, df_podcasts).
    """
    folder = Path(folder)
    audio_files = sorted(folder.glob("Streaming_History_Audio_*.json"))

    if not audio_files:
        raise FileNotFoundError(f"No Streaming_History_Audio_*.json files found in {folder}")

    records = []
    for path in audio_files:
        with open(path, encoding="utf-8") as f:
            records.extend(json.load(f))

    print(f"Loaded {len(records):,} raw records from {len(audio_files)} files")

    df = pd.DataFrame(records)
    df = _clean(df)

    df_tracks   = df[df["content_type"] == "track"].copy()
    df_podcasts = df[df["content_type"] == "podcast"].copy()

    print(f"  → {len(df_tracks):,} music tracks")
    print(f"  → {len(df_podcasts):,} podcast plays")
    print(f"  → Date range: {df_tracks['ts'].min().date()} → {df_tracks['ts'].max().date()}")
    print(f"  → Total listening: {df_tracks['ms_played'].sum() / 3_600_000:.1f} hours")

    return df_tracks, df_podcasts


# ── 2. CLEAN ─────────────────────────────────────────────────────────────────

def _clean(df: pd.DataFrame) -> pd.DataFrame:
    """Full cleaning pipeline — returns enriched DataFrame."""

    # ── 2a. Timestamps ──────────────────────────────────────────────────────
    df["ts"] = pd.to_datetime(df["ts"], utc=True)

    # Local India time (most plays are from IN; adjust if you prefer UTC or US)
    df["ts_local"] = df["ts"].dt.tz_convert("Asia/Kolkata")

    # ── 2b. Content type ─────────────────────────────────────────────────────
    # A record is a track if it has a track URI; a podcast if it has episode info
    df["content_type"] = np.where(
        df["spotify_track_uri"].notna(), "track",
        np.where(df["episode_name"].notna(), "podcast", "other")
    )

    # ── 2c. Tidy column names ────────────────────────────────────────────────
    df = df.rename(columns={
        "master_metadata_track_name":          "track_name",
        "master_metadata_album_artist_name":   "artist_name",
        "master_metadata_album_album_name":    "album_name",
    })

    # ── 2d. Duration in useful units ────────────────────────────────────────
    df["seconds_played"] = df["ms_played"] / 1_000
    df["minutes_played"] = df["ms_played"] / 60_000

    # ── 2e. Temporal features ────────────────────────────────────────────────
    df["year"]         = df["ts_local"].dt.year
    df["month"]        = df["ts_local"].dt.month
    df["month_name"]   = df["ts_local"].dt.strftime("%b")
    df["day_of_week"]  = df["ts_local"].dt.dayofweek          # 0=Mon
    df["dow_name"]     = df["ts_local"].dt.strftime("%a")
    df["hour"]         = df["ts_local"].dt.hour
    df["date"]         = df["ts_local"].dt.date
    ts_naive           = df["ts_local"].dt.tz_localize(None)
    df["year_month"]   = ts_naive.dt.to_period("M")
    df["week"]         = df["ts_local"].dt.isocalendar().week.astype(int)
    df["year_week"]    = ts_naive.dt.to_period("W")

    # Time-of-day bucket
    df["time_of_day"] = pd.cut(
        df["hour"],
        bins=[-1, 5, 11, 16, 20, 23],
        labels=["Night (0-5)", "Morning (6-11)", "Afternoon (12-16)",
                "Evening (17-20)", "Night (21-23)"]
    )

    # ── 2f. Listening behaviour flags ────────────────────────────────────────
    # Was this a meaningful listen? (played > 30 seconds)
    df["meaningful_play"] = df["ms_played"] > 30_000

    # Completion proxy — we don't have track duration, but reason_end gives signal
    df["completed"] = df["reason_end"] == "trackdone"

    # Clean skip flag (Spotify's skipped field + zero-play guard)
    df["skipped"] = df["skipped"].fillna(False).astype(bool)
    df["hard_skip"] = (df["ms_played"] == 0) | (df["reason_end"] == "fwdbtn")

    # ── 2g. Platform normalisation ───────────────────────────────────────────
    def _normalise_platform(p: str) -> str:
        if not isinstance(p, str):
            return "unknown"
        p = p.lower()
        if "android" in p:
            return "Android"
        if "windows" in p:
            return "Windows"
        if "osx" in p or "mac" in p:
            return "macOS"
        if "ios" in p or "iphone" in p or "ipad" in p:
            return "iOS"
        if "web" in p or "browser" in p:
            return "Web"
        return "Other"

    df["platform_clean"] = df["platform"].apply(_normalise_platform)

    # ── 2h. Country label ────────────────────────────────────────────────────
    country_map = {"IN": "India", "US": "United States", "GB": "United Kingdom"}
    df["country"] = df["conn_country"].map(country_map).fillna(df["conn_country"])

    # ── 2i. Drop raw fields we no longer need at the top level ───────────────
    # (keep originals — just makes the useful columns easier to find)

    return df


# ── 3. QUICK SUMMARY ─────────────────────────────────────────────────────────

def summary(df_tracks: pd.DataFrame) -> None:
    """Print a quick overview of the tracks DataFrame."""
    total_hours = df_tracks["ms_played"].sum() / 3_600_000
    top_artist  = df_tracks["artist_name"].value_counts().index[0]
    top_track   = df_tracks["track_name"].value_counts().index[0]
    skip_rate   = df_tracks["skipped"].mean() * 100

    print("=" * 50)
    print("SPOTIFY LISTENING SUMMARY")
    print("=" * 50)
    print(f"Total plays         : {len(df_tracks):,}")
    print(f"Unique artists      : {df_tracks['artist_name'].nunique():,}")
    print(f"Unique tracks       : {df_tracks['track_name'].nunique():,}")
    print(f"Total hours         : {total_hours:,.1f} h")
    print(f"Date range          : {df_tracks['ts'].min().date()} → {df_tracks['ts'].max().date()}")
    print(f"Top artist          : {top_artist}")
    print(f"Most played track   : {top_track}")
    print(f"Skip rate           : {skip_rate:.1f}%")
    print(f"Countries           : {sorted(df_tracks['country'].unique().tolist())}")
    print(f"Platforms           : {sorted(df_tracks['platform_clean'].unique().tolist())}")
    print("=" * 50)


# ── 4. CONVENIENCE SAVERS ────────────────────────────────────────────────────

def save_clean(df_tracks: pd.DataFrame, df_podcasts: pd.DataFrame,
               out_folder: str = ".") -> None:
    """Save cleaned DataFrames to CSV for use in other notebooks."""
    out = Path(out_folder)
    out.mkdir(exist_ok=True)

    # Save with ts as string so CSV round-trips cleanly
    df_tracks.assign(ts=df_tracks["ts"].astype(str),
                     ts_local=df_tracks["ts_local"].astype(str),
                     year_month=df_tracks["year_month"].astype(str),
                     year_week=df_tracks["year_week"].astype(str),
                     date=df_tracks["date"].astype(str)
                     ).to_csv(out / "tracks_clean.csv", index=False)

    df_podcasts.assign(ts=df_podcasts["ts"].astype(str),
                       ts_local=df_podcasts["ts_local"].astype(str),
                       year_month=df_podcasts["year_month"].astype(str),
                       year_week=df_podcasts["year_week"].astype(str),
                       date=df_podcasts["date"].astype(str)
                       ).to_csv(out / "podcasts_clean.csv", index=False)

    print(f"Saved → {out}/tracks_clean.csv")
    print(f"Saved → {out}/podcasts_clean.csv")


# ── 5. ENTRY POINT ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    folder = sys.argv[1] if len(sys.argv) > 1 else "."
    df_tracks, df_podcasts = load_all(folder)
    summary(df_tracks)
    save_clean(df_tracks, df_podcasts, out_folder=folder)