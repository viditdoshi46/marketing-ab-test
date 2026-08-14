"""
Reduce the 600k-row experiment to small aggregate tables the app reads. All the
statistics (z-tests, CIs) run live in the app from these counts, so the repo
stays light and the app stays fast.

Input : data/experiment.csv
Output: data/agg_overall.csv, data/agg_by_<segment>.csv, data/agg_by_exposure.csv
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

DATA = Path(__file__).resolve().parents[1] / "data"


def _counts(df, keys):
    g = df.groupby(keys, observed=True).agg(
        users=("user_id", "size"),
        conversions=("converted", "sum"),
        revenue=("revenue", "sum"),
        unsubscribes=("unsubscribed", "sum"),
    ).reset_index()
    return g


def main():
    df = pd.read_csv(DATA / "experiment.csv")

    _counts(df, ["group"]).to_csv(DATA / "agg_overall.csv", index=False)
    for seg in ["device", "channel", "region"]:
        _counts(df, ["group", seg]).to_csv(DATA / f"agg_by_{seg}.csv", index=False)

    # exposure buckets for a smooth frequency curve
    bins = [0, 2, 4, 6, 8, 10, 12, 100]
    labels = ["1-2", "3-4", "5-6", "7-8", "9-10", "11-12", "13+"]
    df["exposure_bin"] = pd.cut(df["ad_impressions"], bins=bins, labels=labels)
    _counts(df, ["group", "exposure_bin"]).to_csv(DATA / "agg_by_exposure.csv", index=False)

    print("Aggregates written:")
    for f in sorted(DATA.glob("agg_*.csv")):
        print(f"  {f.name:24s} {len(pd.read_csv(f)):>4} rows")


if __name__ == "__main__":
    main()
