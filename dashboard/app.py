"""
app.py
------
Spotify Decoded -- Interactive Dashboard
Run from project root:
    streamlit run dashboard/app.py
"""

import json
from pathlib import Path
from itertools import combinations
from collections import defaultdict

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Spotify Decoded",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Palette ───────────────────────────────────────────────────────────────────
TANGERINE = "#F08C21"
BUTTER    = "#F2D88F"
BLUSH     = "#E36888"
SEA       = "#6698CC"
MATCHA    = "#B4B534"

BG        = "#FDFAF5"
CARD_BG   = "#FFFFFF"
AXIS_COLOR= "#3a3a3a"
GRID_COLOR= "#eeebe4"
TEXT_DARK = "#1a1a1a"
TEXT_MID  = "#555555"

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono:ital,wght@0,400;0,700;1,400&family=Lora:ital,wght@0,400;0,500;1,400&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Lora', serif;
        background-color: {BG};
        color: {TEXT_DARK};
    }}

    .block-container {{
        padding-top: 1.5rem;
        padding-left: 2.5rem;
        padding-right: 2.5rem;
        max-width: 100%;
        background-color: {BG};
    }}

    /* Sidebar */
    [data-testid="stSidebar"] {{
        background-color: #2C1810;
    }}
    [data-testid="stSidebar"] * {{
        color: #f5f0e8 !important;
        font-family: 'Space Mono', monospace !important;
    }}
    [data-testid="stSidebar"] hr {{
        border-color: #4a3020 !important;
    }}

    /* Metric cards */
    [data-testid="metric-container"] {{
        background: {CARD_BG};
        border: 1px solid #ede9e0;
        border-radius: 12px;
        padding: 1rem 1.2rem;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }}
    [data-testid="metric-container"] label {{
        color: {TEXT_MID} !important;
        font-family: 'Space Mono', monospace !important;
        font-size: 0.72rem !important;
        text-transform: uppercase;
        letter-spacing: 0.07em;
    }}
    [data-testid="metric-container"] [data-testid="stMetricValue"] {{
        font-family: 'Space Mono', monospace !important;
        font-size: 1.55rem !important;
        font-weight: 700 !important;
        color: {TEXT_DARK} !important;
    }}

    /* Story callout boxes */
    .story-box {{
        background: {CARD_BG};
        border-left: 4px solid {TANGERINE};
        border-radius: 0 10px 10px 0;
        padding: 1rem 1.4rem;
        margin: 0.5rem 0 1.25rem 0;
        font-family: 'Lora', serif;
        font-size: 0.98rem;
        line-height: 1.75;
        color: {TEXT_DARK};
        box-shadow: 0 1px 4px rgba(0,0,0,0.05);
        font-style: italic;
    }}
    .story-box.blush  {{ border-left-color: {BLUSH}; }}
    .story-box.sea    {{ border-left-color: {SEA}; }}
    .story-box.matcha {{ border-left-color: {MATCHA}; }}

    /* Headers */
    h1 {{
        font-family: 'Space Mono', monospace !important;
        font-size: 2rem !important;
        font-weight: 700 !important;
        color: {TEXT_DARK} !important;
        letter-spacing: -0.03em;
    }}
    h2 {{
        font-family: 'Space Mono', monospace !important;
        font-size: 0.9rem !important;
        font-weight: 700 !important;
        color: {TEXT_DARK} !important;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }}
    h3 {{
        font-family: 'Space Mono', monospace !important;
        font-size: 0.85rem !important;
        font-weight: 400 !important;
        color: {TEXT_MID} !important;
    }}

    /* Subtitle paragraphs */
    .subtitle {{
        font-family: 'Lora', serif;
        font-size: 1.05rem;
        color: {TEXT_MID};
        margin-top: -0.5rem;
        margin-bottom: 0.5rem;
        line-height: 1.6;
    }}

    /* Charts */
    .stPlotlyChart {{ width: 100% !important; }}
    .stPlotlyChart > div {{ width: 100% !important; }}

    /* Dividers */
    hr {{ border-color: #ede9e0 !important; }}

    /* Selectbox and sliders */
    [data-testid="stSelectbox"] label,
    [data-testid="stSlider"] label {{
        font-family: 'Space Mono', monospace !important;
        color: {TEXT_MID} !important;
        font-size: 0.8rem !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}

    /* Selectbox selected value */
    [data-testid="stSelectbox"] div[data-baseweb="select"] span {{
        color: {TEXT_DARK} !important;
        font-family: 'Lora', serif !important;
    }}
    [data-testid="stSelectbox"] div[data-baseweb="select"] {{
        background-color: #ffffff !important;
        border: 1px solid #ddd !important;
    }}

    /* Info box */
    [data-testid="stInfo"] {{
        font-family: 'Space Mono', monospace !important;
        font-size: 0.85rem !important;
        background-color: #fdf6ec !important;
        border-color: {TANGERINE} !important;
    }}
</style>
""", unsafe_allow_html=True)


def story(text, color="tangerine"):
    cls = {"tangerine": "", "blush": "blush",
           "sea": "sea", "matcha": "matcha"}.get(color, "")
    st.markdown(f'<div class="story-box {cls}">{text}</div>',
                unsafe_allow_html=True)


def subtitle(text):
    st.markdown(f'<p class="subtitle">{text}</p>', unsafe_allow_html=True)


def chart_layout(fig, xaxis_title=None, yaxis_title=None, height=380):
    fig.update_layout(
        height        = height,
        plot_bgcolor  = CARD_BG,
        paper_bgcolor = BG,
        margin        = dict(l=10, r=60, t=30, b=10),
        font          = dict(color=AXIS_COLOR, size=11,
                             family="Space Mono"),
        showlegend    = False,
        autosize      = True,
        xaxis=dict(
            title      = xaxis_title,
            color      = AXIS_COLOR,
            tickcolor  = AXIS_COLOR,
            linecolor  = "#ddd",
            gridcolor  = GRID_COLOR,
            title_font = dict(color=AXIS_COLOR, size=11,
                              family="Space Mono"),
            tickfont   = dict(color=AXIS_COLOR, size=10,
                              family="Space Mono"),
        ),
        yaxis=dict(
            title      = yaxis_title,
            color      = AXIS_COLOR,
            tickcolor  = AXIS_COLOR,
            linecolor  = "#ddd",
            gridcolor  = GRID_COLOR,
            title_font = dict(color=AXIS_COLOR, size=11,
                              family="Space Mono"),
            tickfont   = dict(color=AXIS_COLOR, size=10,
                              family="Space Mono"),
        ),
    )
    fig.update_traces(marker_line_width=0)
    return fig


# ── Data loading ──────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    csv_path = Path(__file__).parent.parent / "data" / "processed" / "tracks_clean.csv"
    t = pd.read_csv(csv_path)

    t["ts"]       = pd.to_datetime(t["ts"], utc=True)
    t["ts_local"] = pd.to_datetime(t["ts_local"]).dt.tz_localize("Asia/Kolkata")
    t["date"]     = pd.to_datetime(t["date"])
    t["skipped"]  = t["skipped"].astype(bool)
    t["completed"] = t["completed"].astype(bool)
    t["shuffle"]   = t["shuffle"].astype(bool)
    t["minutes"]   = t["ms_played"] / 60_000
    t["artist"]    = t["artist_name"]
    t["track"]     = t["track_name"]
    t["track_key"] = t["track"] + " ||| " + t["artist"]

    return t
 


@st.cache_data
def build_recommender(tracks):
    t = tracks.sort_values("ts").copy()
    t["gap_min"]     = t["ts"].diff().dt.total_seconds() / 60
    t["new_session"] = t["gap_min"].isna() | (t["gap_min"] > 30)
    t["session_id"]  = t["new_session"].cumsum()

    play_counts = tracks["track_key"].value_counts()
    cooc        = defaultdict(int)
    sequential  = defaultdict(int)

    for sess in t.groupby("session_id")["track_key"].apply(list):
        uniq = list(dict.fromkeys(sess))
        if len(uniq) < 2:
            continue
        for a, b in combinations(uniq, 2):
            cooc[tuple(sorted([a, b]))] += 1
        for i in range(len(sess) - 1):
            a, b = sess[i], sess[i + 1]
            if a != b:
                sequential[(a, b)] += 1

    rows = []
    for (a, b), cnt in cooc.items():
        if cnt < 5:
            continue
        pa  = play_counts.get(a, 1)
        pb  = play_counts.get(b, 1)
        d   = (2 * cnt) / (pa + pb)
        seq = sequential.get((a, b), 0) + sequential.get((b, a), 0)
        sb  = seq / max(pa, pb)
        rows.append({
            "track_a":     a.split(" ||| ")[0],
            "artist_a":    a.split(" ||| ")[1],
            "track_b":     b.split(" ||| ")[0],
            "artist_b":    b.split(" ||| ")[1],
            "cooc_count":  cnt,
            "final_score": round(d + 0.3 * sb, 6),
        })
    return pd.DataFrame(rows)


@st.cache_data
def build_engagement(tracks):
    ts = tracks.groupby(["track", "artist"]).agg(
        plays        = ("track",     "count"),
        completion   = ("completed", "mean"),
        skip_rate    = ("skipped",   "mean"),
        unique_years = ("year",      "nunique"),
    ).reset_index()
    ts["plays_log"]  = np.log1p(ts["plays"])
    ts["engagement"] = (
        0.4 * ts["plays_log"]  / ts["plays_log"].max() +
        0.3 * ts["completion"] +
        0.2 * (1 - ts["skip_rate"]) +
        0.1 * ts["unique_years"] / ts["unique_years"].max()
    )
    lp = tracks.groupby("track")["ts"].max().reset_index()
    lp.columns = ["track", "last_played"]
    return ts.merge(lp, on="track", how="left")


def recommend(track_name, artist_name, sim_df, n=10):
    mask = (
        ((sim_df["track_a"] == track_name) & (sim_df["artist_a"] == artist_name)) |
        ((sim_df["track_b"] == track_name) & (sim_df["artist_b"] == artist_name))
    )
    matches = sim_df[mask].copy()
    if matches.empty:
        return pd.DataFrame()
    results = []
    for _, row in matches.iterrows():
        if row["track_a"] == track_name and row["artist_a"] == artist_name:
            rt, ra = row["track_b"], row["artist_b"]
        else:
            rt, ra = row["track_a"], row["artist_a"]
        score = row["final_score"] * (0.7 if ra == artist_name else 1.0)
        results.append({"track": rt, "artist": ra,
                         "score": round(score, 4),
                         "cooc": row["cooc_count"]})
    return (pd.DataFrame(results)
            .sort_values("score", ascending=False)
            .drop_duplicates(subset=["track", "artist"])
            .head(n))


# ── Load ──────────────────────────────────────────────────────────────────────
tracks = load_data()
sim_df = build_recommender(tracks)
eng_df = build_engagement(tracks)

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.markdown("## 🎵 SPOTIFY DECODED")
st.sidebar.markdown("5.5 years of personal listening data, analyzed.")
st.sidebar.divider()

page = st.sidebar.radio(
    "Navigate",
    ["Overview", "Listening Patterns", "Artists & Tracks", "Recommender"],
    label_visibility="collapsed",
)

year_options  = ["All years"] + sorted(
    tracks["year"].unique().tolist(), reverse=True)
selected_year = st.sidebar.selectbox("Filter by year", year_options)
view          = (tracks[tracks["year"] == selected_year]
                 if selected_year != "All years" else tracks)
show_stories  = selected_year == "All years"

st.sidebar.divider()
st.sidebar.caption("Oct 2020 to Apr 2026")
st.sidebar.caption(f"{len(tracks):,} plays across 5.5 years")

if not show_stories:
    st.info(
        f"Showing data for {selected_year}. "
        "Switch to 'All years' to read the full story."
    )


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 -- OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
if page == "Overview":
    st.title("Spotify Decoded")
    subtitle(
        "5.5 years of listening history, turned into data. "
        "Every play, skip, and session from October 2020 to April 2026."
    )
    st.divider()

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total plays",    f"{len(view):,}")
    c2.metric("Hours listened", f"{view['minutes'].sum()/60:,.0f}")
    c3.metric("Unique artists", f"{view['artist'].nunique():,}")
    c4.metric("Unique tracks",  f"{view['track'].nunique():,}")
    c5.metric("Skip rate",      f"{view['skipped'].mean()*100:.1f}%")

    st.divider()

    if show_stories:
        story(
            "Music has always been my companion. Something to lean on when things "
            "get heavy, something to celebrate with when they go well, something "
            "that just sits with you when you need company. "
            "Over 5.5 years that relationship left a data trail. "
            "This is what it looks like.",
            color="tangerine",
        )

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Hours per year")
        yearly = (tracks.groupby("year")["minutes"]
                  .sum().div(60).round(1).reset_index())
        yearly.columns = ["Year", "Hours"]
        colors = [TANGERINE if h == yearly["Hours"].max() else BUTTER
                  for h in yearly["Hours"]]
        fig = go.Figure(go.Bar(
            x=yearly["Year"], y=yearly["Hours"],
            marker_color=colors,
            text=yearly["Hours"].astype(int),
            textposition="outside",
            textfont=dict(color=AXIS_COLOR, size=10,
                          family="Space Mono"),
        ))
        fig = chart_layout(fig, xaxis_title="Year", yaxis_title="Hours")
        fig.update_xaxes(
            tickmode="array",
            tickvals=yearly["Year"].tolist(),
            ticktext=yearly["Year"].astype(str).tolist(),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Monthly listening heatmap")
        monthly = (tracks.groupby(["year","month"])["minutes"]
                   .sum().div(60).round(1).unstack(fill_value=0))
        monthly.columns = ["Jan","Feb","Mar","Apr","May","Jun",
                            "Jul","Aug","Sep","Oct","Nov","Dec"]
        fig = px.imshow(
            monthly,
            color_continuous_scale=[[0, BUTTER], [0.5, TANGERINE], [1, BLUSH]],
            aspect="auto", text_auto=".0f",
        )
        fig.update_layout(
            height=380, plot_bgcolor=CARD_BG, paper_bgcolor=BG,
            margin=dict(l=10, r=10, t=10, b=10),
            coloraxis_showscale=False,
            font=dict(color=AXIS_COLOR, size=10, family="Space Mono"),
            xaxis=dict(tickfont=dict(color=AXIS_COLOR, size=10,
                                     family="Space Mono")),
            yaxis=dict(tickfont=dict(color=AXIS_COLOR, size=10,
                                     family="Space Mono")),
        )
        st.plotly_chart(fig, use_container_width=True)

    if show_stories:
        peak_year  = yearly.loc[yearly["Hours"].idxmax(), "Year"]
        peak_hours = yearly["Hours"].max()
        story(
            f"2025 is the peak at {peak_hours:.0f} hours and I am not surprised. "
            "2024 was the year I moved from India to the US, and when you are trying "
            "to figure out a new country and a new life, you are not really sitting "
            "still long enough to listen to music. "
            "2025 was when I finally stopped running and music was right there waiting. "
            "It ended up being one of the harder years personally, "
            "and the data quietly reflects that.",
            color="blush",
        )

    st.divider()
    col3, col4 = st.columns(2)

    with col3:
        st.subheader("Where the listening happened")
        cd = view["country"].value_counts().reset_index()
        cd.columns = ["Country", "Plays"]
        fig = px.pie(
            cd, values="Plays", names="Country",
            color_discrete_sequence=[TANGERINE, SEA, MATCHA],
            hole=0.45,
        )
        fig.update_layout(
            height=340, paper_bgcolor=BG,
            margin=dict(l=10, r=10, t=10, b=10),
            font=dict(color=AXIS_COLOR, size=10, family="Space Mono"),
            legend=dict(font=dict(color=AXIS_COLOR, family="Space Mono")),
            showlegend=True,
        )
        fig.update_traces(textfont=dict(color="white", size=11,
                                        family="Space Mono"))
        st.plotly_chart(fig, use_container_width=True)

    with col4:
        st.subheader("Platform")
        pd_data = (view[view["platform"] != "Other"]["platform"]
                   .value_counts().reset_index())
        pd_data.columns = ["Platform", "Plays"]
        plat_colors = {"Android": TANGERINE, "Windows": SEA, "macOS": MATCHA}
        colors = [plat_colors.get(p, BUTTER) for p in pd_data["Platform"]]
        fig = go.Figure(go.Bar(
            x=pd_data["Platform"], y=pd_data["Plays"],
            marker_color=colors,
            text=pd_data["Plays"].apply(lambda x: f"{x:,}"),
            textposition="outside",
            textfont=dict(color=AXIS_COLOR, size=10, family="Space Mono"),
        ))
        fig = chart_layout(fig, xaxis_title="", yaxis_title="Plays")
        st.plotly_chart(fig, use_container_width=True)

    if show_stories:
        story(
            "Almost everything was on Android. Phone in hand, earphones in, wherever I was. "
            "Windows was the study setup back in India. "
            "The macOS slice only starts in late August 2025 when I got a new laptop, "
            "so that bar is about 8 months of data compared to 5 years of everything else.",
            color="sea",
        )


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 -- LISTENING PATTERNS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Listening Patterns":
    st.title("Listening Patterns")
    subtitle(
        "When, how, and with what intention. The behavioural layer of the data."
    )
    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("When do you listen?")
        hourly = view.groupby("hour").size().reset_index(name="Plays")
        hourly.columns = ["Hour", "Plays"]
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=hourly["Hour"], y=hourly["Plays"],
            mode="lines",
            line=dict(color=TANGERINE, width=2.5),
            fill="tozeroy",
            fillcolor="rgba(240,140,33,0.12)",
        ))
        fig = chart_layout(fig, xaxis_title="Hour of day (local time)",
                           yaxis_title="Play count")
        fig.update_xaxes(
            tickmode="array",
            tickvals=list(range(0, 24, 2)),
            ticktext=[f"{h:02d}:00" for h in range(0, 24, 2)],
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Day of week")
        dow_order = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
        dow = (view.groupby("dow_name").size()
               .reindex(dow_order).reset_index())
        dow.columns = ["Day", "Plays"]
        dow_colors = [BLUSH if p == dow["Plays"].max() else BUTTER
                      for p in dow["Plays"]]
        fig = go.Figure(go.Bar(
            x=dow["Day"], y=dow["Plays"],
            marker_color=dow_colors,
        ))
        fig = chart_layout(fig, xaxis_title="", yaxis_title="Play count")
        st.plotly_chart(fig, use_container_width=True)

    if show_stories:
        story(
            "The 8am peak makes complete sense. That was the bus to uni every morning, "
            "earphones in, sometimes half asleep, always listening. "
            "The late night numbers are a different story. "
            "In 2021 barely anything played past midnight. "
            "By 2025 that number had crossed 6,000 plays. "
            "Music at 2am hits differently when you actually need it.",
            color="tangerine",
        )

    st.divider()
    col3, col4 = st.columns(2)

    with col3:
        st.subheader("Hour x day heatmap")
        hm = view.groupby(["dow","hour"]).size().unstack(fill_value=0)
        hm.index = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
        fig = px.imshow(
            hm,
            color_continuous_scale=[[0, "#fdf8f0"],
                                     [0.5, BUTTER],
                                     [1, TANGERINE]],
            aspect="auto",
        )
        fig.update_layout(
            height=340, plot_bgcolor=CARD_BG, paper_bgcolor=BG,
            margin=dict(l=10, r=10, t=10, b=10),
            coloraxis_showscale=False,
            font=dict(color=AXIS_COLOR, size=10, family="Space Mono"),
            xaxis=dict(
                title="Hour of day",
                tickfont=dict(color=AXIS_COLOR, size=10, family="Space Mono"),
                title_font=dict(color=AXIS_COLOR, size=11,
                                family="Space Mono"),
            ),
            yaxis=dict(
                tickfont=dict(color=AXIS_COLOR, size=10, family="Space Mono"),
            ),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col4:
        st.subheader("Skip rate by year")
        sr = (tracks.groupby("year")["skipped"]
              .mean().mul(100).round(1).reset_index())
        sr.columns = ["Year", "Skip Rate (%)"]
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=sr["Year"], y=sr["Skip Rate (%)"],
            mode="lines+markers",
            line=dict(color=BLUSH, width=2.5),
            marker=dict(size=8, color=BLUSH),
        ))
        fig = chart_layout(fig, xaxis_title="Year",
                           yaxis_title="Skip rate (%)")
        fig.update_xaxes(
            tickmode="array",
            tickvals=sr["Year"].tolist(),
            ticktext=sr["Year"].astype(str).tolist(),
        )
        st.plotly_chart(fig, use_container_width=True)

    if show_stories:
        story(
            "The 0% skip rate in 2020 and 2021 is a data issue, not a miracle. "
            "Spotify did not record it in older exports. "
            "From 2022 the numbers are real. "
            "The skip rate climbing in 2025 alongside the highest ever play count "
            "just means I was searching more that year, cycling through songs "
            "until I found the one that fit the moment.",
            color="blush",
        )

    st.divider()
    st.subheader("Shuffle vs intentional listening")

    if show_stories:
        story(
            "About 40% of plays had shuffle on. "
            "When shuffle is off the skip rate drops by almost half, "
            "which makes sense. Intentional listening means "
            "you actually wanted to hear that song.",
            color="sea",
        )

    shuffle_stats = (view.groupby("shuffle").agg(
        plays      = ("track",     "count"),
        skip_pct   = ("skipped",   lambda x: round(x.mean()*100, 1)),
        completion = ("completed", lambda x: round(x.mean()*100, 1)),
    ).reset_index())
    shuffle_stats["shuffle"] = shuffle_stats["shuffle"].map(
        {True: "Shuffle", False: "Intentional"})

    c1, c2, c3 = st.columns(3)
    for col, metric, ytitle, color in zip(
        [c1, c2, c3],
        ["plays",  "skip_pct",      "completion"],
        ["Plays",  "Skip rate (%)", "Completion rate (%)"],
        [SEA,      BLUSH,           MATCHA],
    ):
        fig = go.Figure(go.Bar(
            x=shuffle_stats["shuffle"],
            y=shuffle_stats[metric],
            marker_color=[color, BUTTER],
            text=shuffle_stats[metric].astype(str),
            textposition="outside",
            textfont=dict(color=AXIS_COLOR, size=10, family="Space Mono"),
        ))
        fig = chart_layout(fig, xaxis_title="", yaxis_title=ytitle,
                           height=320)
        col.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 -- ARTISTS & TRACKS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Artists & Tracks":
    st.title("Artists & Tracks")
    subtitle(
        "Who gets the most hours, which tracks never got old, "
        "and what the data reveals about listening depth."
    )
    st.divider()

    if show_stories:
        story(
            "503 hours of NCT DREAM. That is 21 full days of one group. "
            "Their music sits in a sweet spot for me, not too heavy, not too soft, "
            "just the right amount of everything. "
            "The kind of music that works whether you are happy, exhausted, "
            "or somewhere in between. "
            "The data just confirms what I already knew.",
            color="tangerine",
        )

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Top artists by hours")
        n_artists = st.slider("Number of artists", 5, 25, 15, key="n_art")
        ta = (view.groupby("artist")["minutes"]
              .sum().div(60).sort_values(ascending=False)
              .head(n_artists).reset_index())
        ta.columns = ["Artist", "Hours"]
        bar_colors = [TANGERINE if i == 0 else BLUSH if i < 3 else BUTTER
                      for i in range(len(ta))]
        fig = go.Figure(go.Bar(
            x=ta["Hours"], y=ta["Artist"],
            orientation="h",
            marker_color=bar_colors,
            text=ta["Hours"].apply(lambda x: f"{x:.0f}h"),
            textposition="outside",
            textfont=dict(color=AXIS_COLOR, size=10, family="Space Mono"),
        ))
        fig = chart_layout(fig, xaxis_title="Hours", yaxis_title="",
                           height=max(380, n_artists * 30))
        fig.update_layout(yaxis=dict(
            autorange="reversed",
            tickfont=dict(color=AXIS_COLOR, size=10, family="Space Mono"),
        ))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Top tracks by play count")
        n_tracks = st.slider("Number of tracks", 5, 25, 15, key="n_tr")
        tt = view["track"].value_counts().head(n_tracks).reset_index()
        tt.columns = ["Track", "Plays"]
        tr_colors = [BLUSH if i == 0 else TANGERINE if i < 3 else BUTTER
                     for i in range(len(tt))]
        fig = go.Figure(go.Bar(
            x=tt["Plays"], y=tt["Track"],
            orientation="h",
            marker_color=tr_colors,
            text=tt["Plays"].astype(str),
            textposition="outside",
            textfont=dict(color=AXIS_COLOR, size=10, family="Space Mono"),
        ))
        fig = chart_layout(fig, xaxis_title="Plays", yaxis_title="",
                           height=max(380, n_tracks * 30))
        fig.update_layout(yaxis=dict(
            autorange="reversed",
            tickfont=dict(color=AXIS_COLOR, size=10, family="Space Mono"),
        ))
        st.plotly_chart(fig, use_container_width=True)

    if show_stories:
        story(
            "1,112 plays of Teddy Bear. First listen March 2022, "
            "last recorded play January 2026. "
            "It is a song about offering comfort, about being there for someone "
            "when things feel heavy. "
            "Most of those plays happened on the bus home from uni, often half asleep. "
            "There is something about a song that keeps finding you across four years "
            "and two different countries that is hard to explain with data alone.",
            color="blush",
        )

    st.divider()
    st.subheader("Artist engagement")
    st.caption(
        "Completion rate vs skip rate. "
        "Bubble size = total plays. Hover for details."
    )

    ast = view.groupby("artist").agg(
        plays          = ("track",     "count"),
        hours          = ("minutes",   lambda x: x.sum()/60),
        completion_pct = ("completed", lambda x: round(x.mean()*100, 1)),
        skip_pct       = ("skipped",   lambda x: round(x.mean()*100, 1)),
    ).reset_index()
    ast = ast[ast["plays"] >= 50]

    fig = px.scatter(
        ast, x="completion_pct", y="skip_pct",
        size="plays", color="hours",
        hover_name="artist",
        hover_data={"plays": True, "hours": ":.0f",
                    "completion_pct": True, "skip_pct": True},
        color_continuous_scale=[[0, BUTTER], [0.5, TANGERINE], [1, BLUSH]],
        size_max=45,
        labels={
            "completion_pct": "Completion rate (%)",
            "skip_pct":       "Skip rate (%)",
            "hours":          "Total hours",
        },
    )
    fig.update_layout(
        height=460, plot_bgcolor=CARD_BG, paper_bgcolor=BG,
        margin=dict(l=10, r=10, t=10, b=10),
        font=dict(color=AXIS_COLOR, size=10, family="Space Mono"),
        xaxis=dict(
            title="Completion rate (%)",
            tickfont=dict(color=AXIS_COLOR, size=10, family="Space Mono"),
            title_font=dict(color=AXIS_COLOR, size=11, family="Space Mono"),
            gridcolor=GRID_COLOR, linecolor="#ddd",
        ),
        yaxis=dict(
            title="Skip rate (%)",
            tickfont=dict(color=AXIS_COLOR, size=10, family="Space Mono"),
            title_font=dict(color=AXIS_COLOR, size=11, family="Space Mono"),
            gridcolor=GRID_COLOR, linecolor="#ddd",
        ),
        coloraxis_colorbar=dict(
            title="Hours",
            tickfont=dict(color=AXIS_COLOR, family="Space Mono"),
            title_font=dict(color=AXIS_COLOR, family="Space Mono"),
        ),
    )
    st.plotly_chart(fig, use_container_width=True)

    if show_stories:
        story(
            "The bottom right is where the committed listening lives, "
            "low skips and high completion. "
            "The top left is browsing mode, searching for the right song "
            "rather than settling into one. "
            "Most of the Tamil and Telugu artists end up there not because "
            "I like them less but because that is how I listen to that music. "
            "More active, more searching, looking for the one that matches "
            "exactly how I feel right now.",
            color="matcha",
        )

    st.divider()
    st.subheader("Forgotten favourites")
    st.caption("High engagement tracks not played since Jan 2025.")

    if show_stories:
        story(
            "These tracks were genuinely loved at some point. "
            "Strong play counts, high completion, low skips. "
            "Most of them are ENHYPEN and TXT from 2023 and early 2024. "
            "They did not disappear because I stopped liking them. "
            "2025 just brought a lot of new things to feel, "
            "and the playlist shifted with it.",
            color="sea",
        )

    cutoff   = pd.Timestamp("2025-01-01", tz="UTC")
    forgotten = eng_df[
        (eng_df["engagement"] > 0.6) &
        (eng_df["last_played"] < cutoff) &
        (eng_df["plays"] >= 20)
    ].sort_values("engagement", ascending=False).head(15)

    st.dataframe(
        forgotten[["track","artist","plays","engagement"]]
        .rename(columns={
            "track":      "Track",
            "artist":     "Artist",
            "plays":      "Plays",
            "engagement": "Engagement",
        })
        .assign(Engagement=lambda x: x["Engagement"].round(3))
        .reset_index(drop=True),
        use_container_width=True,
        hide_index=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 4 -- RECOMMENDER
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Recommender":
    st.title("Track Recommender")
    subtitle(
        "Built from 5,485 listening sessions. "
        "No audio features, no external database. "
        "Just patterns in how tracks were listened to together."
    )
    st.divider()

    if show_stories:
        story(
            "I tried three ways to build this with proper audio features. "
            "Spotify deprecated their API in 2024. "
            "A 1.2 million track Kaggle dataset matched only 37% of my catalog "
            "because most of my music is K-pop and South Indian, "
            "not well covered by Western databases. Last.fm managed 11%. "
            "So I built it from session patterns instead, from the 5,485 times "
            "I sat down and chose what to listen to. "
            "What tracks kept appearing together, what I always played back to back. "
            "It ended up being more personal than any API could have been.",
            color="tangerine",
        )

    track_options = (tracks.groupby(["track","artist"])
                     .size().reset_index(name="plays")
                     .sort_values("plays", ascending=False))
    track_options["label"] = (track_options["track"]
                               + " -- " + track_options["artist"])

    selected_label  = st.selectbox(
        "Search for a track",
        track_options["label"].tolist(),
        index=0,
    )
    selected_row    = track_options[
        track_options["label"] == selected_label].iloc[0]
    selected_track  = selected_row["track"]
    selected_artist = selected_row["artist"]
    n_recs          = st.slider("Number of recommendations", 5, 20, 10)

    st.divider()
    recs = recommend(selected_track, selected_artist, sim_df, n=n_recs)

    if recs.empty:
        st.info(
            "Not enough co-occurrence data for this track. "
            "Try a track with more plays."
        )
    else:
        col1, col2 = st.columns([3, 1])

        with col1:
            st.subheader(
                f"Tracks alongside '{selected_track}'"
            )
            bar_colors = [
                TANGERINE if i == 0 else BLUSH if i < 3 else BUTTER
                for i in range(len(recs))
            ]
            fig = go.Figure(go.Bar(
                x=recs["score"], y=recs["track"],
                orientation="h",
                marker_color=bar_colors,
                text=recs["artist"],
                textposition="outside",
                textfont=dict(color=AXIS_COLOR, size=10,
                              family="Space Mono"),
                customdata=np.stack(
                    [recs["artist"], recs["cooc"]], axis=-1),
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "Artist: %{customdata[0]}<br>"
                    "Sessions together: %{customdata[1]}<br>"
                    "Score: %{x:.4f}<extra></extra>"
                ),
            ))
            fig = chart_layout(
                fig, xaxis_title="Similarity score",
                height=max(380, n_recs * 38),
            )
            fig.update_layout(yaxis=dict(
                autorange="reversed",
                tickfont=dict(color=AXIS_COLOR, size=10,
                              family="Space Mono"),
            ))
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Track stats")
            eng_row = eng_df[
                (eng_df["track"]  == selected_track) &
                (eng_df["artist"] == selected_artist)
            ]
            if not eng_row.empty:
                r = eng_row.iloc[0]
                st.metric("Total plays",     f"{int(r['plays']):,}")
                st.metric("Completion rate", f"{r['completion']*100:.1f}%")
                st.metric("Skip rate",       f"{r['skip_rate']*100:.1f}%")
                st.metric("Engagement",      f"{r['engagement']:.3f}")

            st.divider()
            st.dataframe(
                recs[["track","artist","cooc"]]
                .rename(columns={
                    "track":  "Track",
                    "artist": "Artist",
                    "cooc":   "Sessions",
                }),
                use_container_width=True,
                hide_index=True,
                height=360,
            )