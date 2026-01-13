import pandas as pd


# Paths
shoot_path = "epl_shooting_clean.csv"
pass_path = "epl_passing_clean.csv"
def_path = "epl_defensive_clean.csv"
poss_path = "epl_possession_clean.csv"
tm_path = "epl_tm_clean.csv"


# Load
shoot = pd.read_csv(shoot_path)
passing = pd.read_csv(pass_path)
defn = pd.read_csv(def_path)
poss = pd.read_csv(poss_path)
tm = pd.read_csv(tm_path)


# Common key set
key_cols = ["player_key", "club_key", "season", "league"]


# Merge FBref tables step by step (left joins on shooting base)
base = shoot.copy()


base = base.merge(
passing.drop(columns=["player_name", "club", "position", "nation_raw", "nation_code"], errors="ignore"),
on=key_cols,
how="left",
suffixes=("", "_pass")
)


base = base.merge(
defn.drop(columns=["player_name", "club", "position", "nation_raw", "nation_code"], errors="ignore"),
on=key_cols,
how="left",
suffixes=("", "_def")
)


base = base.merge(
poss.drop(columns=["player_name", "club", "position", "nation_raw", "nation_code"], errors="ignore"),
on=key_cols,
how="left",
suffixes=("", "_poss")
)


# Merge Transfermarkt
full = base.merge(
tm[["player_key", "club_key", "season", "league",
"player_name", "club", "position", "market_value_eur", "market_value_millions"]],
on=key_cols,
how="left",
suffixes=("", "_tm")
)


# Prefer FBref display names when present
full["player_name_final"] = full["player_name"].fillna(full["player_name_tm"])
full["club_final"] = full.get("club", full.get("club_tm"))


# Filter to players with some real playing time (e.g. >= 10 90s)
if "nineties" in full.columns:
  full = full[full["nineties"] >= 10]


# Save intermediate joined table
full.to_csv("epl_player_joined_raw.csv", index=False, encoding="utf-8-sig")
print("Joined shape:", full.shape)
print(full.head())