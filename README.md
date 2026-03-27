# FinanceImpact — Market Intelligence Platform

**v6** — 7-stage ML sentiment pipeline · Live charts · Corporate ripple effect

## Quick Start

```bash
pip install -r requirements.txt
streamlit run app.py
```

Set `FI_DEV_MODE=1` to enable demo accounts (admin/admin123, demo/demo1234).

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `FI_DEV_MODE` | `0` | Set `1` to enable dev mode + demo accounts |
| `FI_ADMIN_PASSWORD` | — | Admin account password (required in prod) |
| `FI_DEMO_PASSWORD` | — | Demo account password (required in prod) |
| `FI_GUEST_PASSWORD` | — | Guest account password (required in prod) |
| `FI_MAX_ATTEMPTS` | `5` | Login rate-limit attempts before lockout |
| `FI_LOCKOUT_SECONDS` | `300` | Lockout duration in seconds |
| `FI_BCRYPT_ROUNDS` | `12` | bcrypt work factor |

## Architecture

```
app.py            — Entry point, Streamlit navigation, bootstrap
pages/
  0_Home.py       — Landing, stats, quick access
  1_Dashboard.py  — 7-stage ML headline analyzer
  2_News.py       — Live RSS news feed
  3_Watchlist.py  — Portfolio watchlist + price alerts
  4_History.py    — Analysis history with timeline
  5_Settings.py   — User preferences, security, data management
  6_Market.py     — Full market charts + indicators
core/
  constants.py    — Shared ticker names, example headlines
  engine.py       — ML pipeline (pure Python, no Streamlit)
  feeds.py        — RSS feed fetcher (parallel)
  graph.py        — Corporate hierarchy + ripple propagation
  seeder.py       — Sample data generation
  stocks.py       — yFinance wrapper + technical indicators
db/
  schema.py       — SQLite DDL + seed users
  ops.py          — All CRUD operations with retry logic
ui/
  auth.py         — Session management, login/register
  components.py   — HTML component builders
  nav.py          — Sidebar navigation
  theme.py        — Global CSS injection
data/
  corporate_hierarchy.json  — NetworkX graph source
  finance_impact.db         — SQLite database (auto-created)
```

## ML Pipeline (v6)

| Stage | Module | Description |
|---|---|---|
| 1 · NER | engine.detect_entities | Keyword-based entity detection |
| 2 · Event | engine.classify_event | Regex event classification (9 types) |
| 3 · FinBERT | engine.finbert_score | Financial sentiment + keyword fallback |
| 4 · Rumour | engine.detect_rumour | Multi-signal credibility scoring |
| 5 · SHAP | engine.word_attributions | Weighted lexicon word attribution |
| 6 · Historical | engine.find_similar | Sentence-transformer similarity (TF-IDF fallback) |
| 7 · Macro | engine.macro_context | VIX-based amplification factor |

## Key Fixes in v6

- **Critical**: Pagination in History page now correctly renders the paginated slice
- **Critical**: Login form submit checked inside `with st.form()` context
- **Critical**: `init_db()` connection always closed via context manager
- `add_watch()` correctly returns False for duplicates
- `do_logout()` only deletes `_fi_` prefixed session keys
- `engine.py` has zero Streamlit imports (pure Python)
- TF-IDF fallback for historical similarity fully implemented
- Ticker filter uses exact token matching (not `str.contains`)
- News Strongest Signals shows top 5 by absolute polarity
- Watchlist 90-day chart >6 tickers shows info message
- Price alert default handles None/0 prices safely
- History Clear All has confirmation dialog
- Settings export is single-click download
- Account deletion option added
- `ON DELETE CASCADE` on all FK relationships
- Retry logic on SQLite lock errors
- numpy scalar types serialized correctly in JSON export
