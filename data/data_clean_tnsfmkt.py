import pandas as pd
import unicodedata
import re
import os

# ---------- CONFIG ----------
RAW_TM_PATH = "Transfermkt.csv"              # your file
CLEAN_TM_PATH = "epl_tm_clean.csv"
SEASON_LABEL = "2024-25"                     # set to match your FBref season
LEAGUE_LABEL = "Premier League"


# ---------- HELPER FUNCTIONS ----------

def normalize_name(s: str) -> str:
    """Lowercase, strip, and remove accents for robust joining."""
    if pd.isna(s):
        return ""
    s = str(s).strip().lower()
    s = "".join(
        c for c in unicodedata.normalize("NFKD", s)
        if not unicodedata.combining(c)
    )
    return s

def parse_market_value(v):
    """Convert '€150.00m' / '€10.00m' / '€800k' to numeric euros."""
    if pd.isna(v):
        return None
    s = str(v).strip().lower()
    # remove euro sign, spaces, commas
    s = s.replace("€", "").replace(",", "").strip()
    multiplier = 1.0
    if s.endswith("m"):
        multiplier = 1e6
        s = s[:-1]
    elif s.endswith("k"):
        multiplier = 1e3
        s = s[:-1]
    # keep only digits and dot
    s = re.sub(r"[^0-9.]", "", s)
    if not s:
        return None
    try:
        return float(s) * multiplier
    except ValueError:
        return None


# ---------- LOAD RAW DATA (ROBUST ENCODING) ----------

try:
    print(f"Reading {RAW_TM_PATH} as UTF-8 CSV...")
    tm_raw = pd.read_csv(RAW_TM_PATH, encoding="utf-8")
except UnicodeDecodeError:
    print("UTF-8 failed; trying latin-1...")
    tm_raw = pd.read_csv(RAW_TM_PATH, encoding="latin-1")

print("Raw columns:", list(tm_raw.columns))
# Expect: ['Name', 'Position', 'Value', 'Team']


# ---------- RENAME COLUMNS ----------

rename_map = {
    "Name": "player_name",
    "Position": "position",
    "Value": "market_value_raw",
    "Team": "club"
}
tm = tm_raw.rename(columns=rename_map)


# ---------- ADD SEASON & LEAGUE ----------

tm["season"] = SEASON_LABEL
tm["league"] = LEAGUE_LABEL


# ---------- PARSE MARKET VALUE ----------

tm["market_value_eur"] = tm["market_value_raw"].apply(parse_market_value)
tm["market_value_millions"] = tm["market_value_eur"] / 1e6


# ---------- CLEAN POSITION TEXT (LIGHT) ----------

tm["position"] = tm["position"].astype(str).str.strip()


# ---------- CREATE JOIN KEYS (MATCHING FBREF SCRIPTS) ----------

tm["player_key"] = tm["player_name"].apply(normalize_name)
tm["club_key"] = tm["club"].apply(normalize_name)


# ---------- OPTIONAL FILTER: DROP ROWS WITHOUT VALUE ----------

tm = tm[tm["market_value_eur"].notna()]


# ---------- SAVE CLEANED FILE ----------

tm.to_csv(CLEAN_TM_PATH, index=False, encoding="utf-8-sig")
print(f"Saved cleaned Transfermarkt data to: {os.path.abspath(CLEAN_TM_PATH)}")
print(tm.head())
