"""
Generate a realistic marketing A/B test: a new ad campaign (treatment) vs. the
existing creative (control), randomized across ~600k users.

The data has genuine structure so the analysis is interesting and defensible:
  * a real (but modest) treatment lift on conversion,
  * a HETEROGENEOUS effect (bigger lift on mobile) so segmentation matters,
  * an exposure-frequency curve with DIMINISHING RETURNS and mild FATIGUE at
    high frequency, so there's an "optimal exposure cap" to recommend,
  * a guardrail metric (unsubscribe rate) that must not get worse.

Deterministic (seeded).

Table written to data/:
  experiment.csv  (one row per user)

Usage:  python src/make_data.py
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

DATA = Path(__file__).resolve().parents[1] / "data"
DATA.mkdir(parents=True, exist_ok=True)
RNG = np.random.default_rng(42)

N = 600_000
DEVICES = ["Mobile", "Desktop", "Tablet"]
DEVICE_P = [0.62, 0.31, 0.07]
CHANNELS = ["Paid Search", "Social", "Display", "Email"]
CHANNEL_P = [0.34, 0.33, 0.18, 0.15]
REGIONS = ["West", "South", "Northeast", "Midwest"]
REGION_P = [0.28, 0.30, 0.22, 0.20]


def _sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def main():
    group = RNG.choice(["control", "treatment"], N, p=[0.5, 0.5])
    device = RNG.choice(DEVICES, N, p=DEVICE_P)
    channel = RNG.choice(CHANNELS, N, p=CHANNEL_P)
    region = RNG.choice(REGIONS, N, p=REGION_P)

    # ad exposures (impressions) per user: skewed, 1..~20
    exposures = np.clip(RNG.poisson(4, N) + 1, 1, 25)

    is_tx = (group == "treatment").astype(float)
    mobile = (device == "Mobile").astype(float)

    # ---- conversion propensity (control baseline ~2.8%) ----
    base = -3.62                                   # ~2.8% baseline conversion
    # channel & device intercepts (realistic differences)
    ch_int = pd.Series(channel).map(
        {"Paid Search": 0.35, "Social": 0.0, "Display": -0.35, "Email": 0.20}).values
    dev_int = pd.Series(device).map(
        {"Mobile": 0.0, "Desktop": 0.12, "Tablet": -0.10}).values

    # treatment lift: small +0.09 logit, extra +0.08 on mobile (heterogeneous)
    tx_effect = is_tx * (0.09 + 0.08 * mobile)

    # exposure curve: concave gain (centered near the mean exposure) that peaks
    # then fatigues past ~8 impressions -> supports an "optimal exposure cap".
    exp_gain = (0.12 * (np.log1p(exposures) - np.log1p(4))
                - 0.020 * np.clip(exposures - 8, 0, None))

    z = base + ch_int + dev_int + tx_effect + exp_gain
    p_conv = _sigmoid(z)
    converted = (RNG.random(N) < p_conv).astype(int)

    # revenue for converters (log-normal), slightly higher for treatment
    revenue = np.where(
        converted == 1,
        np.round(np.exp(RNG.normal(4.0 + 0.05 * is_tx, 0.5)), 2), 0.0)

    # guardrail: unsubscribe. Rises a touch with heavy exposure (fatigue) but the
    # treatment itself does NOT increase it -> guardrail passes.
    p_unsub = _sigmoid(-4.2 + 0.05 * np.clip(exposures - 8, 0, None))
    unsubscribed = (RNG.random(N) < p_unsub).astype(int)

    df = pd.DataFrame({
        "user_id": np.arange(1, N + 1),
        "group": group, "device": device, "channel": channel, "region": region,
        "ad_impressions": exposures, "converted": converted,
        "revenue": revenue, "unsubscribed": unsubscribed,
    })
    df.to_csv(DATA / "experiment.csv", index=False)

    g = df.groupby("group")["converted"].mean()
    lift = g["treatment"] / g["control"] - 1
    print(f"users={len(df):,}  control={g['control']*100:.2f}%  "
          f"treatment={g['treatment']*100:.2f}%  relative lift={lift*100:.1f}%")
    print(f"mobile lift check: "
          f"{df[df.device=='Mobile'].groupby('group').converted.mean().to_dict()}")


if __name__ == "__main__":
    main()
