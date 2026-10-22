# Book Stores Dashboard (Task 4)

Data from 5 book stores (STORE1 - STORE5) is cleaned, analyzed and shown in a Streamlit dashboard.
The dashboard also has an AI chat (Gemini). The AI does not count anything itself,
it calls Python functions from `tools.py` to get exact numbers.

For every store the dashboard shows:
- top 5 days by revenue
- number of unique users (one person can have several user ids)
- number of unique author sets
- most popular author (or author set) by sold books
- best buyer with all his user ids
- daily revenue chart

Every store has its own tab, the last tab is the AI chat.

## How to run

```
pip install -r requirements.txt
python clean_data.py
python analysis.py
streamlit run app.py
```

`clean/` and `results/` are already in the repo, so you can also start only the app.

## Gemini key

The AI chat needs a Gemini API key. Put it in `.streamlit/secrets.toml`:

```
GEMINI_API_KEY = "your key"
```

This file is in `.gitignore`, do not commit it.
On Streamlit Community Cloud add the same line in the app settings (Secrets).

## Files

- `intro.ipynb` - first look at the data
- `clean_data.py` - reads `data/`, fixes types, prices (EUR to USD) and dates, saves to `clean/`
- `analysis.py` - finds the results for every store and saves them to `results/` (json, csv, png)
- `tools.py` - functions that the AI calls to get numbers
- `chat.py` - Gemini client and chat
- `app.py` - Streamlit dashboard with the AI chat tab
- `data/` - raw data
- `clean/` - cleaned data
- `results/` - results of the analysis
