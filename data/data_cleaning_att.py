import pandas as pd
import unicodedata
import os

# ---------- CONFIG ----------
RAW_SHOOTING_PATH = "EPL_Shooting_1.csv"        # update if needed
CLEAN_SHOOTING_PATH = "epl_shooting_clean.csv"
SEASON_LABEL = "2024-25"                        # adjust to match this file
LEAGUE_LABEL = "Premier League"

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


# ---------- ROBUST LOAD (LIKE YOUR SHOOTING SCRIPT) ----------

input_file = RAW_SHOOTING_PATH

try:
    print(f"Attempting to read '{input_file}' as UTF-8 CSV (header on row 2)...")
    # header=1 because FBref export usually has a first row with title info
    shoot_raw = pd.read_csv(input_file, header=1, encoding="utf-8")
except UnicodeDecodeError:
    print("UTF-8 read failed. Trying with 'latin-1'...")
    shoot_raw = pd.read_csv(input_file, header=1, encoding="latin-1")
except pd.errors.ParserError:
    print("CSV parsing failed. Trying read_excel()...")
    shoot_raw = pd.read_excel(input_file, header=1)

print("Raw columns:", list(shoot_raw.columns))


# ---------- DROP UNNEEDED COLUMNS ----------

cols_to_drop = ["Rk"]
for col in cols_to_drop:
    if col in shoot_raw.columns:
        shoot_raw = shoot_raw.drop(columns=col)


# ---------- BASIC CLEANING OF NATION (KEEP CAPS ONLY) ----------

if "Nation" in shoot_raw.columns:
    shoot_raw["Nation"] = shoot_raw["Nation"].astype(str)
    shoot_raw["nation_code"] = shoot_raw["Nation"].apply(extract_country_code)


# ---------- DO *NOT* SPLIT MULTI-POSITION ROWS ----------
# Keep Pos as-is; derive a single position_group instead.

# ---------- RENAME COLUMNS TO SNAKE_CASE ----------

rename_map = {
    "Player": "player_name",
    "Nation": "nation_raw",  # keep raw, we already created nation_code
    "Pos": "position",
    "Squad": "club",
    "Age": "age",
    "Born": "born",
    "90s": "nineties",
    "Gls": "goals",
    "Sh": "shots",
    "SoT": "shots_on_target",
    "Sh/90": "shots_per90",
    "SoT/90": "sot_per90",
    "G/Sh": "goals_per_shot",
    "G/SoT": "goals_per_sot",
    "Dist": "avg_shot_distance",
    "FK": "free_kicks",
    "PK": "penalty_goals",
    "PKatt": "penalty_attempts",
    "xG": "xg",
    "npxG": "npxg",
    "npxG/Sh": "npxg_per_shot",
    "G-xG": "g_minus_xg",
    "np:G-xG": "npg_minus_npxg",
}

shoot_df = shoot_raw.rename(columns=rename_map)


# ---------- ADD SEASON & LEAGUE ----------

shoot_df["season"] = SEASON_LABEL
shoot_df["league"] = LEAGUE_LABEL


# ---------- NUMERIC CONVERSION ----------

numeric_cols = [
    "age", "nineties",
    "goals", "shots", "shots_on_target",
    "shots_per90", "sot_per90",
    "goals_per_shot", "goals_per_sot",
    "avg_shot_distance",
    "free_kicks", "penalty_goals", "penalty_attempts",
    "xg", "npxg", "npxg_per_shot",
    "g_minus_xg", "npg_minus_npxg",
]

existing_numeric = [c for c in numeric_cols if c in shoot_df.columns]

for col in existing_numeric:
    shoot_df[col] = pd.to_numeric(shoot_df[col], errors="coerce")

# Optional: fill NaNs with 0 for stats (but not Age)
cols_to_fill_zero = [c for c in existing_numeric if c != "age"]
shoot_df[cols_to_fill_zero] = shoot_df[cols_to_fill_zero].fillna(0)


# ---------- CREATE KEYS & POSITION GROUP ----------

shoot_df["player_key"] = shoot_df["player_name"].apply(normalize_name)
shoot_df["club"] = shoot_df["club"].apply(standardize_club_fbref)
shoot_df["club_key"] = shoot_df["club"].apply(normalize_name)
shoot_df["position_group"] = shoot_df["position"].apply(position_group)


# ---------- FILTER OUT OBVIOUS NON-PLAYERS (LIKE YOUR EARLIER SCRIPT) ----------

if {"nineties", "shots", "xg"}.issubset(shoot_df.columns):
    shoot_df = shoot_df[~((shoot_df["nineties"] == 0) &
                          (shoot_df["shots"] == 0) &
                          (shoot_df["xg"] == 0))]


# ---------- SAVE WITH UTF-8-SIG FOR EXCEL COMPATIBILITY ----------

shoot_df.to_csv(CLEAN_SHOOTING_PATH, index=False, encoding="utf-8-sig")
print(f"Saved cleaned shooting data to: {os.path.abspath(CLEAN_SHOOTING_PATH)}")
print(shoot_df.head())
