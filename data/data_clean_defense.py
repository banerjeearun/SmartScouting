import pandas as pd
import unicodedata
import os

# ---------- CONFIG ----------
RAW_DEF_PATH = "EPL_Defensive.csv"          # update if needed
CLEAN_DEF_PATH = "epl_defensive_clean.csv"
SEASON_LABEL = "2024-25"                    # set to your season
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

def extract_country_code(nation: str) -> str:
    """
    From values like 'eng ENG', 'ci CIV', 'br BRA',
    keep only the uppercase 3-letter code (ENG, CIV, BRA).
    """
    if pd.isna(nation):
        return ""
    parts = str(nation).split()
    last = parts[-1]
    return "".join(ch for ch in last if ch.isupper())

def position_group(pos: str) -> str:
    if pd.isna(pos):
        return "Other"
    pos = str(pos)
    if "GK" in pos:
        return "GK"
    if "DF" in pos:
        return "DF"
    if "MF" in pos:
        return "MF"
    if "FW" in pos:
        return "FW"
    return "Other"

CLUB_MAP_FBREF_TO_CANON = {
    "Ipswich Town": "Ipswich",
    "Leicester City": "Leicester",
    "Manchester City": "Man City",
    "Manchester Utd": "Man Utd",
    "Newcastle Utd": "Newcastle",
    "Nott'ham Forest": "Nottm Forest"
}

def standardize_club_fbref(club):
    if pd.isna(club):
        return club
    club = str(club).strip()
    return CLUB_MAP_FBREF_TO_CANON.get(club, club)



# ---------- ROBUST LOAD ----------

input_file = RAW_DEF_PATH

try:
    print(f"Attempting to read '{input_file}' as UTF-8 CSV...")
    def_raw = pd.read_csv(input_file,header=1, encoding="utf-8")
except UnicodeDecodeError:
    print("UTF-8 read failed. Trying with 'latin-1'...")
    def_raw = pd.read_csv(input_file,header=1, encoding="latin-1")
except pd.errors.ParserError:
    print("CSV parsing failed. Trying read_excel()...")
    def_raw = pd.read_excel(input_file,header=1)

print("Raw columns:", list(def_raw.columns))


# ---------- DROP UNNEEDED COLUMNS ----------

cols_to_drop = ["Rk", "Matches"]
for col in cols_to_drop:
    if col in def_raw.columns:
        def_raw = def_raw.drop(columns=col)


# ---------- NATION CODE ----------

if "Nation" in def_raw.columns:
    def_raw["Nation"] = def_raw["Nation"].astype(str)
    def_raw["nation_code"] = def_raw["Nation"].apply(extract_country_code)


# ---------- RENAME COLUMNS TO SNAKE_CASE ----------

rename_map = {
    "Player": "player_name",
    "Nation": "nation_raw",
    "Pos": "position",
    "Squad": "club",
    "Age": "age",
    "Born": "born",
    "90s": "nineties",
    "Tkl": "tackles",
    "TklW": "tackles_won",
    "Def 3rd": "tackles_def_3rd",
    "Mid 3rd": "tackles_mid_3rd",
    "Att 3rd": "tackles_att_3rd",
    "Tkl_dribbler": "tackles_vs_dribblers",
    "Att": "dribbles_faced",
    "Tkl%": "tackle_success_pct",
    "Lost": "dribbles_lost",
    "Blocks": "blocks",
    "Sh": "blocks_shots",
    "Pass": "blocks_passes",
    "Int": "interceptions",
    "Tkl+Int": "tackles_plus_interceptions",
    "Clr": "clearances",
    "Err": "errors_leading_to_shot"
}

def_df = def_raw.rename(columns=rename_map)


# ---------- ADD SEASON & LEAGUE ----------

def_df["season"] = SEASON_LABEL
def_df["league"] = LEAGUE_LABEL


# ---------- NUMERIC CONVERSION ----------

numeric_cols = [
    "age", "nineties",
    "tackles", "tackles_won",
    "tackles_def_3rd", "tackles_mid_3rd", "tackles_att_3rd",
    "tackles_vs_dribblers", "dribbles_faced",
    "tackle_success_pct", "dribbles_lost",
    "blocks", "blocks_shots", "blocks_passes",
    "interceptions", "tackles_plus_interceptions",
    "clearances", "errors_leading_to_shot"
]

existing_numeric = [c for c in numeric_cols if c in def_df.columns]

for col in existing_numeric:
    def_df[col] = pd.to_numeric(def_df[col], errors="coerce")

# Optional: fill NaNs with 0 for stats (but not Age)
cols_to_fill_zero = [c for c in existing_numeric if c != "age"]
def_df[cols_to_fill_zero] = def_df[cols_to_fill_zero].fillna(0)


# ---------- KEYS & POSITION GROUP ----------

def_df["player_key"] = def_df["player_name"].apply(normalize_name)
def_df["club"] = def_df["club"].apply(standardize_club_fbref)
def_df["club_key"] = def_df["club"].apply(normalize_name)
def_df["position_group"] = def_df["position"].apply(position_group)


# ---------- OPTIONAL FILTER: DROP 0 MINUTES ----------

if "nineties" in def_df.columns:
    def_df = def_df[def_df["nineties"] > 0]


# ---------- SAVE CLEAN FILE ----------

def_df.to_csv(CLEAN_DEF_PATH, index=False, encoding="utf-8-sig")
print(f"Saved cleaned defensive data to: {os.path.abspath(CLEAN_DEF_PATH)}")
print(def_df.head())
