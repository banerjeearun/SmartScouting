import numpy as np
import pandas as pd

# ---------------------------------------------------------
# 1. LOAD DATA
# ---------------------------------------------------------
df = pd.read_csv("epl_player_joined_raw.csv")

# Filter out Goalkeepers (They require completely different stats)
df = df[df["position_group"] != "GK"].copy()

# Basic Safety: Replace 0 minutes with NaN to avoid division by zero
df["nineties"] = df["nineties"].replace(0, np.nan)


# ---------------------------------------------------------
# 2. FEATURE ENGINEERING (RAW PER 90 SCORES)
# ---------------------------------------------------------

# A. Attacking Score (Goals + Non-Penalty xG)
# We use npxG to measure threat without penalty inflation
df["raw_attacking"] = (
    df["goals"].fillna(0) / df["nineties"] +
    df["npxg"].fillna(0) / df["nineties"]
)

# B. Progression Score (Moving the ball)
# Passes that move the ball 10 yards or into the box + Carries
df["raw_progression"] = (
    df["progressive_passes"].fillna(0) / df["nineties"] +
    df["progressive_carries"].fillna(0) / df["nineties"]
)

# C. Creation Score (The final ball)
# Assists + Expected Assisted Goals (xAG)
df["raw_creation"] = (
    df["assists"].fillna(0) / df["nineties"] +
    df["xag"].fillna(0) / df["nineties"]
)

# D. Defensive Activity Score
# Tackles + Interceptions + Blocks + Clearances
# Note: 'recoveries' was excluded as it wasn't in your initial column list
df["raw_defensive"] = (
    df["tackles_plus_interceptions"].fillna(0) / df["nineties"] +
    df["blocks"].fillna(0) / df["nineties"] +
    df["clearances"].fillna(0) / df["nineties"]
)

# E. Mistakes Score (Negative Impact)
# Losing the ball via failed dribble or bad touch
df["raw_mistakes"] = (
    df["dispossessed"].fillna(0) / df["nineties"] +
    df["miscontrols"].fillna(0) / df["nineties"]
)


# ---------------------------------------------------------
# 3. NORMALIZATION (Z-SCORES)
# ---------------------------------------------------------
# This puts all stats on the same scale (Mean = 0, Std Dev = 1)
# Vital so that "50 passes" doesn't outweigh "0.5 goals"

features_to_scale = [
    "raw_attacking", 
    "raw_progression", 
    "raw_creation", 
    "raw_defensive", 
    "raw_mistakes"
]

for col in features_to_scale:
    # Calculate mean and std for the whole league
    mu = df[col].mean()
    sigma = df[col].std()
    
    # Create the Z-score column (e.g., z_raw_attacking)
    df[f"z_{col}"] = (df[col] - mu) / sigma


# ---------------------------------------------------------
# 4. PERFORMANCE INDEX
# ---------------------------------------------------------

def calculate_index(row):
    pg = row.get("position_group", "")
    
    # Grab the Z-scores
    att = row["z_raw_attacking"]
    prog = row["z_raw_progression"]
    creat = row["z_raw_creation"]
    defs = row["z_raw_defensive"]
    mistakes = row["z_raw_mistakes"]
    
    # Weighted Formula based on Position
    if pg == "FW":
        # Forwards: Heavily favor Attacking & Creation
        score = (0.50 * att) + (0.15 * prog) + (0.25 * creat) + (0.10 * defs) - (0.15 * mistakes)
        
    elif pg == "MF":
        # Midfielders: Balanced, high emphasis on Progression
        score = (0.15 * att) + (0.35 * prog) + (0.25 * creat) + (0.25 * defs) - (0.15 * mistakes)
        
    elif pg == "DF":
        # Defenders: Heavily favor Defense, but reward Progression (Modern CBs)
        score = (0.05 * att) + (0.20 * prog) + (0.05 * creat) + (0.70 * defs) - (0.15 * mistakes)
        
    else:
        # Fallback (Equal weights)
        score = att + prog + creat + defs - mistakes
        
    return score

df["performance_index"] = df.apply(calculate_index, axis=1)


# ---------------------------------------------------------
# 5. VALUATION ANALYSIS
# ---------------------------------------------------------

# Rank Percentiles (0.0 to 1.0) within Position Groups
df["perf_rank_pct"] = df.groupby("position_group")["performance_index"].rank(pct=True)
df["value_rank_pct"] = df.groupby("position_group")["market_value_millions"].rank(pct=True)

# The Delta: How much better is their play than their price?
df["undervaluation_delta"] = df["perf_rank_pct"] - df["value_rank_pct"]

def categorize_valuation(delta):
    # If Performance percentile is >25% higher than Value percentile
    if delta > 0.25:
        return "Undervalued"
    # If Performance percentile is >15% lower than Value percentile
    if delta < -0.15:
        return "Overvalued"
    return "Fair Value"

df["valuation_category"] = df["undervaluation_delta"].apply(categorize_valuation)


# ---------------------------------------------------------
# 6. SAVE & CLEANUP
# ---------------------------------------------------------

cols_to_round = [
    "performance_index", 
    "undervaluation_delta", 
    "perf_rank_pct", 
    "value_rank_pct",
    "raw_attacking",
    "raw_progression",
    "raw_creation",
    "raw_defensive",
    "raw_mistakes"
]

for col in cols_to_round:
    if col in df.columns:
        df[col] = df[col].round(4)

df.to_csv("epl_player_data_final_v2.csv", index=False, encoding="utf-8-sig")
print("Process Complete. File saved as 'epl_player_data_final_v2.csv'")
print(df[["player_name", "position_group", "performance_index", "valuation_category"]].head(10))