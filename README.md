# Smart Scouting For Undervalued Players

Explore the full interactive report and visualization suite here: <https://banerjeearun.github.io/SmartScouting/>

## Overview

Recruitment in football is broken. Clubs routinely pay a "Winner's Tax," overspending on hype and past reputation while ignoring statistical reality.

This project is a data analytics suite designed to identify market inefficiencies in the English Premier League (2024-25 season). By combining performance metrics (FBref) with financial valuations (Transfermarkt), we aim to uncover "High-Efficiency Outliers"—players producing elite-level output on mid-table budgets.

The goal is simple: Replicate the output of a title contender without spending a title contender’s budget.

## Key Features & Analysis

This project moves beyond basic "Goals and Assists" analysis, utilizing advanced statistical techniques to create a comprehensive recruitment strategy:

* The Player Atlas (PCA): Using Principal Component Analysis to map the entire league into 2D space, identifying unique tactical profiles (e.g., "The Chaos Agents" like Darwin Núñez vs. "Safe Distributors").

* Tactical DNA Tests (Parallel Coordinates): Finding "Functional Clones." We prove that affordable targets (e.g., Bryan Mbeumo) share the exact geometric statistical profile as elite superstars (e.g., Bukayo Saka).

* The Inefficiency Gap (Dumbbell Plots): Visualizing the delta between Cost Rank and Performance Rank.

* The League Landscape: Assessing team efficiency (Squad Value vs. Total Performance Index) to identify "Smart Markets" for scouting.

## Dataset & Engineering

The analysis is built on a custom dataset (epl_player_data_final_v2.csv) containing 297 players and 125 attributes.

### Data Sources

* Performance: Scraped from FBref (via StatsBomb) using worldfootballR. Includes xG, xAG, Progressive Actions, Defensive Actions, and Possession metrics.

* Financial: Market values and position data scraped from Transfermarkt.

### Data Pipeline (Python)

* Cleaning & Transformation: All data cleaning, merging, and initial preprocessing were handled using Python.

Location: The raw Python scripts used for this ETL (Extract, Transform, Load) process are located directly in the data/ folder.
