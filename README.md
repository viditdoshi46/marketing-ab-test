# Marketing A/B Test — Conversion Lift Analysis

**Business question:** A growth team ran a new ad creative against the existing one on ~600k users. Three questions decide whether it ships: **Did it lift conversion? For whom? And how often should we show it?**

**Headline results:**

- The new creative lifted conversion from **3.07% to 3.43%** — a **+0.36 pp / +11.5% relative** lift that is **statistically significant** (two-proportion z-test, z = 7.7, p ≈ 1e-14). The 95% confidence interval on the lift, **[0.27, 0.44] pp**, sits entirely above zero, so the win is real, not noise.
- The effect is **heterogeneous**: it's strongest on **Mobile** — so a capacity- or budget-constrained rollout should start there.
- **Frequency matters.** Conversion rises with ad exposures, **peaks around 7–8 impressions**, then flattens while the unsubscribe (fatigue) rate keeps climbing — pointing to a **frequency cap** that protects both budget and the guardrail metric.
- **Guardrail check passes:** the treatment did not increase unsubscribes, so the conversion win isn't quietly hurting retention.

**Decision: ship the campaign, roll out to mobile first, and cap frequency near the conversion peak.**

---

## What the app does

An interactive Streamlit app with four views:

1. **Results** — the headline lift, significance, confidence interval, revenue-per-user, and the guardrail check, with a clear ship/no-ship verdict.
2. **Segments** — a separate z-test for every device, channel, and region, surfacing the mobile-driven heterogeneity.
3. **Exposure & Frequency** — the conversion-vs-frequency curve with the fatigue (unsubscribe) overlay and a recommended frequency cap.
4. **Calculator & Methodology** — a live A/B calculator (plug in any two groups), a **sample-size / power planner**, and a plain-English explanation of every statistic used.

▶ **Live app:** _deploy to Streamlit Community Cloud and drop the link here._

## Concepts demonstrated

Two-proportion z-test, p-values and their correct interpretation, confidence intervals on the lift, **statistical power and minimum detectable effect (MDE)**, **guardrail metrics**, **heterogeneous treatment effects** (segmentation), **frequency capping / ad fatigue**, and the **peeking problem** (why you fix sample size up front).

## Reproduce

```bash
pip install -r requirements.txt
python run_all.py                      # generate data → small aggregates
streamlit run app/streamlit_app.py
```

## A note on the data

Runs offline on a **synthetic experiment** (`src/make_data.py`) with realistic, planted structure: a modest true lift, a bigger effect on mobile, a concave exposure curve with fatigue, and a guardrail that holds. All statistics run **live from pre-aggregated counts**, so the repo stays light and the app stays fast.

*Built by Vidit Doshi · Experiment design · statistics · Python · Streamlit*
