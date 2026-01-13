import pandas as pd
import unicodedata
import os

# ---------- CONFIG ----------
RAW_PASSING_PATH = "EPL_Passing.csv"          # update if needed
CLEAN_PASSING_PATH = "epl_passing_clean.csv"
SEASON_LABEL = "2024-25"                      # change if different season
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


# ---------- ROBUST LOAD (LIKE SHOOTING SCRIPT) ----------

input_file = RAW_PASSING_PATH

try:
    print(f"Attempting to read '{input_file}' as UTF-8 CSV...")
    pass_raw = pd.read_csv(input_file, encoding="utf-8")
except UnicodeDecodeError:
    print("UTF-8 read failed. Trying with 'latin-1'...")
    pass_raw = pd.read_csv(input_file, encoding="latin-1")
except pd.errors.ParserError:
    print("CSV parsing failed. Trying read_excel()...")
    pass_raw = pd.read_excel(input_file)

print("Raw columns:", list(pass_raw.columns))


# ---------- DROP CLEARLY UNNEEDED COLUMNS ----------

cols_to_drop = ["Rk", "Born"]
for col in cols_to_drop:
    if col in pass_raw.columns:
        pass_raw = pass_raw.drop(columns=col)


# ---------- RENAME COLUMNS TO SNAKE_CASE ----------

rename_map = {
    "Player": "player_name",
    "Nation": "nation",
    "Pos": "position",
    "Squad": "club",
    "Age": "age",
    "90s": "nineties",
    "tot_Cmp": "passes_completed_total",
    "tot_Att": "passes_attempted_total",
    "tot_Cmp%": "pass_completion_total_pct",
    "TotDist": "pass_total_distance",
    "tot_PrgDist": "pass_progressive_distance",
    "shrt_Cmp": "short_passes_completed",
    "shrt_Att": "short_passes_attempted",
    "shrt_Cmp%": "short_pass_completion_pct",
    "med_Cmp": "medium_passes_completed",
    "med_Att": "medium_passes_attempted",
    "med_Cmp%": "medium_pass_completion_pct",
    "lng_Cmp": "long_passes_completed",
    "lng_Att": "long_passes_attempted",
    "lng_Cmp%": "long_pass_completion_pct",
    "Ast": "assists",
    "xAG": "xag",
    "xA": "xa",
    "A-xAG": "a_minus_xag",
    "KP": "key_passes",
    "1-Mar": "passes_into_final_third",  # or 1/3 depending on FBref header
    "PPA": "passes_into_pen_area",
    "CrsPA": "crosses_into_pen_area",
    "PrgP": "progressive_passes",
}

pass_df = pass_raw.rename(columns=rename_map)


# ---------- ADD SEASON & LEAGUE ----------

pass_df["season"] = SEASON_LABEL
pass_df["league"] = LEAGUE_LABEL


# ---------- ENSURE NUMERIC TYPES ----------

numeric_cols = [
    "age", "nineties",
    "passes_completed_total", "passes_attempted_total",
    "pass_completion_total_pct",
    "pass_total_distance", "pass_progressive_distance",
    "short_passes_completed", "short_passes_attempted",
    "short_pass_completion_pct",
    "medium_passes_completed", "medium_passes_attempted",
    "medium_pass_completion_pct",
    "long_passes_completed", "long_passes_attempted",
    "long_pass_completion_pct",
    "assists", "xag", "xa", "a_minus_xag",
    "key_passes", "passes_into_final_third",
    "passes_into_pen_area", "crosses_into_pen_area",
    "progressive_passes",
]

for col in numeric_cols:
    if col in pass_df.columns:
        pass_df[col] = pd.to_numeric(pass_df[col], errors="coerce")


# ---------- KEYS, NATION CODE, POSITION GROUP ----------

# Keep original accented name for display (player_name)
# Use accent-stripped, lowercase key for joins

pass_df["player_key"] = pass_df["player_name"].apply(normalize_name)
pass_df["club"] = pass_df["club"].apply(standardize_club_fbref)
pass_df["club_key"] = pass_df["club"].apply(normalize_name)

# Only the CAPS part of Nation
if "nation" in pass_df.columns:
    pass_df["nation_code"] = pass_df["nation"].apply(extract_country_code)

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

pass_df["position_group"] = pass_df["position"].apply(position_group)


# ---------- OPTIONAL FILTER: DROP 0 MINUTES ----------

if "nineties" in pass_df.columns:
    pass_df = pass_df[pass_df["nineties"] > 0]


# ---------- SAVE WITH UTF-8-SIG (LIKE SHOOTING SCRIPT) ----------

pass_df.to_csv(CLEAN_PASSING_PATH, index=False, encoding="utf-8-sig")
print(f"Saved cleaned passing data to: {os.path.abspath(CLEAN_PASSING_PATH)}")
print(pass_df.head())
