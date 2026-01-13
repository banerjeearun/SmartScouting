import pandas as pd
import unicodedata
import os

# ---------- CONFIG ----------
RAW_POSSESSION_PATH = "EPL_Possession.csv"          # update if needed
CLEAN_POSSESSION_PATH = "epl_possession_clean.csv"
SEASON_LABEL = "2024-25"                            # set to your season
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

input_file = RAW_POSSESSION_PATH

try:
    print(f"Attempting to read '{input_file}' as UTF-8 CSV...")
    poss_raw = pd.read_csv(input_file,header=1,  encoding="utf-8")
except UnicodeDecodeError:
    print("UTF-8 read failed. Trying with 'latin-1'...")
    poss_raw = pd.read_csv(input_file, header=1, encoding="latin-1")
except pd.errors.ParserError:
    print("CSV parsing failed. Trying read_excel()...")
    poss_raw = pd.read_excel(input_file, header=1)

print("Raw columns:", list(poss_raw.columns))


# ---------- DROP UNNEEDED COLUMNS ----------

cols_to_drop = ["Rk", "Matches"]
for col in cols_to_drop:
    if col in poss_raw.columns:
        poss_raw = poss_raw.drop(columns=col)


# ---------- NATION CODE ----------

if "Nation" in poss_raw.columns:
    poss_raw["Nation"] = poss_raw["Nation"].astype(str)
    poss_raw["nation_code"] = poss_raw["Nation"].apply(extract_country_code)


# ---------- RENAME COLUMNS TO SNAKE_CASE ----------

rename_map = {
    "Player": "player_name",
    "Nation": "nation_raw",
    "Pos": "position",
    "Squad": "club",
    "Age": "age",
    "Born": "born",
    "90s": "nineties",
    "Touches": "touches",
    "Def Pen": "touches_def_pen",
    "Def 3rd": "touches_def_3rd",
    "Mid 3rd": "touches_mid_3rd",
    "Att 3rd": "touches_att_3rd",
    "Att Pen": "touches_att_pen",
    "Live": "touches_live",
    "Att": "takeons_attempted",
    "Succ": "takeons_succeeded",
    "Succ%": "takeons_success_pct",
    "Tkld": "takeons_tackled",
    "Tkld%": "takeons_tackled_pct",
    "Carries": "carries",
    "TotDist": "carries_total_distance",
    "PrgDist": "carries_progressive_distance",
    "PrgC": "progressive_carries",
    "1-Mar": "carries_into_final_third",     # or 1/3 depending on FBref header
    "CPA": "carries_into_pen_area",
    "Mis": "miscontrols",
    "Dis": "dispossessed",
    "Rec": "passes_received",
    "PrgR": "progressive_passes_received",
}

poss_df = poss_raw.rename(columns=rename_map)


# ---------- ADD SEASON & LEAGUE ----------

poss_df["season"] = SEASON_LABEL
poss_df["league"] = LEAGUE_LABEL


# ---------- NUMERIC CONVERSION ----------

numeric_cols = [
    "age", "nineties",
    "touches", "touches_def_pen", "touches_def_3rd", "touches_mid_3rd",
    "touches_att_3rd", "touches_att_pen", "touches_live",
    "takeons_attempted", "takeons_succeeded", "takeons_success_pct",
    "takeons_tackled", "takeons_tackled_pct",
    "carries", "carries_total_distance", "carries_progressive_distance",
    "progressive_carries", "carries_into_final_third",
    "carries_into_pen_area", "miscontrols", "dispossessed",
    "passes_received", "progressive_passes_received",
]

existing_numeric = [c for c in numeric_cols if c in poss_df.columns]

for col in existing_numeric:
    poss_df[col] = pd.to_numeric(poss_df[col], errors="coerce")

# Optional: fill NaNs with 0 for stats (but not Age)
cols_to_fill_zero = [c for c in existing_numeric if c != "age"]
poss_df[cols_to_fill_zero] = poss_df[cols_to_fill_zero].fillna(0)


# ---------- KEYS & POSITION GROUP ----------

poss_df["player_key"] = poss_df["player_name"].apply(normalize_name)
poss_df["club"] = poss_df["club"].apply(standardize_club_fbref)
poss_df["club_key"] = poss_df["club"].apply(normalize_name)
poss_df["position_group"] = poss_df["position"].apply(position_group)


# ---------- OPTIONAL FILTER: DROP 0 MINUTES ----------

if "nineties" in poss_df.columns:
    poss_df = poss_df[poss_df["nineties"] > 0]


# ---------- SAVE CLEAN FILE ----------

poss_df.to_csv(CLEAN_POSSESSION_PATH, index=False, encoding="utf-8-sig")
print(f"Saved cleaned possession data to: {os.path.abspath(CLEAN_POSSESSION_PATH)}")
print(poss_df.head())
