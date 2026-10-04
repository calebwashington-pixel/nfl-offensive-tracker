"""
NFL Offense Efficiency Tracker
------------------------------
Ranks every NFL offense from Week 1 on, using the free nflverse play-by-play data.

Install once:
    pip install pandas polars pyarrow
    pip install "nflreadpy@git+https://github.com/nflverse/nflreadpy"

Run once:
    python nfl_offense_tracker.py

Keep it running and refresh every 30 minutes:
    python nfl_offense_tracker.py --refresh 30

Each run saves two CSV files you can chart later:
    offense_season.csv   one row per team (the leaderboard)
    offense_weekly.csv   one row per team per week (for trend lines)
"""

import argparse
import time
from datetime import datetime

import pandas as pd


def load_plays(season):
    """Download the season's play-by-play and keep real offensive plays."""
    import nflreadpy as nfl  # imported here so the rest works without it

    df = nfl.load_pbp(season).to_pandas()
    df = df[(df["season_type"] == "REG") & df["play_type"].isin(["pass", "run"])]
    return df.dropna(subset=["posteam", "epa"])


def summarize(plays, by):
    """Compute the metrics for each group. `by` is ['posteam'] or ['posteam', 'week']."""
    plays = plays.copy()

    # A play is "explosive" if it's a 20+ yard pass or a 10+ yard run
    plays["explosive"] = (
        ((plays["play_type"] == "pass") & (plays["yards_gained"] >= 20))
        | ((plays["play_type"] == "run") & (plays["yards_gained"] >= 10))
    ).astype(int)

    # Flag pass/run plays so we can average each one separately
    plays["pass_epa"] = plays["epa"].where(plays["play_type"] == "pass")
    plays["rush_epa"] = plays["epa"].where(plays["play_type"] == "run")

    # Third down conversion: only count 3rd downs
    plays["third_down_conv"] = plays["first_down"].where(plays["down"] == 3)

    table = plays.groupby(by).agg(
        plays=("epa", "size"),
        epa_per_play=("epa", "mean"),
        success_rate=("success", "mean"),
        pass_epa=("pass_epa", "mean"),
        rush_epa=("rush_epa", "mean"),
        explosive_rate=("explosive", "mean"),
        third_down_pct=("third_down_conv", "mean"),
        yards_per_play=("yards_gained", "mean"),
    )

    # Turn rates into percentages and round everything to be readable
    for col in ["success_rate", "explosive_rate", "third_down_pct"]:
        table[col] = table[col] * 100
    return table.round(3).reset_index().rename(columns={"posteam": "team"})


def run_once(season):
    plays = load_plays(season)
    season_table = summarize(plays, ["posteam"])
    season_table = season_table.sort_values("epa_per_play", ascending=False)
    season_table.insert(0, "rank", range(1, len(season_table) + 1))
    weekly_table = summarize(plays, ["posteam", "week"])

    season_table.to_csv("offense_season.csv", index=False)
    weekly_table.to_csv("offense_weekly.csv", index=False)

    last_week = int(plays["week"].max())
    print(f"\n{season} offense rankings through Week {last_week} "
          f"(updated {datetime.now():%b %d, %I:%M %p})")
    print(season_table.to_string(index=False))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", type=int, default=2026)
    parser.add_argument("--refresh", type=int, default=0,
                        help="re-run every N minutes (0 = run once)")
    args = parser.parse_args()

    while True:
        try:
            run_once(args.season)
        except Exception as error:  # keep the loop alive if the download hiccups
            print(f"Update failed: {error}")
        if args.refresh == 0:
            break
        time.sleep(args.refresh * 60)


if __name__ == "__main__":
    main()
