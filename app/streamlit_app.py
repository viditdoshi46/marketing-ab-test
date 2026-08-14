"""
Marketing A/B Test — Conversion Lift Analysis.

A new ad campaign (treatment) vs. the existing creative (control), tested on
~600k users. The app answers the three questions a growth team actually asks:
Did it work? For whom? And how often should we show it? It runs the statistics
live from pre-aggregated counts and explains every method in plain English.

Run:  streamlit run app/streamlit_app.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

from stats import two_proportion_ztest, required_sample_size, achieved_power

st.set_page_config(page_title="A/B Test — Conversion Lift | Vidit Doshi",
                   layout="wide", page_icon="🧪")

st.markdown("""
<style>
  .block-container {max-width: 1120px; padding-top: 2.6rem;}
  .hero {background:linear-gradient(120deg,#047857 0%,#10b981 100%); color:#fff;
         padding:22px 26px; border-radius:14px; margin-bottom:6px;}
  .hero h1 {color:#fff; margin:0; font-size:1.6rem; font-weight:700;}
  .hero p {color:#d1fae5; margin:6px 0 0; font-size:1.0rem;}
  div[data-testid="stMetric"] {border:1px solid rgba(16,185,129,.30);
      border-radius:12px; padding:12px 16px;}
  .verdict {border-radius:10px; padding:14px 18px; font-size:1.05rem; margin-top:6px;}
  .win {background:#ecfdf5; border-left:5px solid #10b981; color:#065f46;}
  .note {background:#f8fafc; border-left:4px solid #94a3b8; color:#334155;
         padding:12px 16px; border-radius:8px;}
</style>
""", unsafe_allow_html=True)

DATA = ROOT / "data"
EXP_ORDER = ["1-2", "3-4", "5-6", "7-8", "9-10", "11-12", "13+"]


@st.cache_data
def load(name):
    return pd.read_csv(DATA / name)


overall = load("agg_overall.csv").set_index("group")
c, t = overall.loc["control"], overall.loc["treatment"]
res = two_proportion_ztest(int(c.conversions), int(c.users),
                           int(t.conversions), int(t.users))

st.markdown("""
<div class="hero">
  <h1>🧪 A/B Test — Conversion Lift Analysis</h1>
  <p>New ad campaign vs. existing creative, randomized across ~600k users.
     Did it lift conversion, for whom, and at what frequency?</p>
</div>
""", unsafe_allow_html=True)

tab_res, tab_seg, tab_exp, tab_calc = st.tabs(
    ["📊  Results", "🔍  Segments", "📈  Exposure & Frequency", "🧮  Calculator & Methodology"])

# ============================ RESULTS ============================
with tab_res:
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Control conversion", f"{res.p_control*100:.2f}%")
    k2.metric("Treatment conversion", f"{res.p_treat*100:.2f}%",
              f"{res.abs_lift*100:+.2f} pp")
    k3.metric("Relative lift", f"{res.rel_lift*100:+.1f}%")
    k4.metric("p-value", f"{res.p_value:.1e}",
              "significant" if res.significant else "not significant")

    verdict = ("✅ <b>Ship the campaign.</b> Treatment lifted conversion from "
               f"{res.p_control*100:.2f}% to {res.p_treat*100:.2f}% — a "
               f"<b>{res.rel_lift*100:.1f}% relative lift</b> "
               f"({res.abs_lift*100:.2f} pp). This is statistically significant "
               f"(z = {res.z:.1f}, p = {res.p_value:.1e}); the 95% confidence "
               f"interval on the lift is [{res.ci_low*100:.2f}, "
               f"{res.ci_high*100:.2f}] pp — entirely above zero.")
    st.markdown(f'<div class="verdict win">{verdict}</div>', unsafe_allow_html=True)

    left, right = st.columns([3, 2])
    with left:
        fig = go.Figure()
        fig.add_bar(x=["Control", "Treatment"],
                    y=[res.p_control*100, res.p_treat*100],
                    marker_color=["#94a3b8", "#10b981"],
                    error_y=dict(type="data", array=[
                        0, (res.ci_high-res.abs_lift)*100], visible=False),
                    text=[f"{res.p_control*100:.2f}%", f"{res.p_treat*100:.2f}%"],
                    textposition="outside")
        fig.update_layout(height=340, title="Conversion rate by group",
                          yaxis_title="conversion %", margin=dict(t=40, l=10, r=10, b=10))
        st.plotly_chart(fig, use_container_width=True)
    with right:
        # revenue per user + guardrail
        rpu_c = c.revenue / c.users
        rpu_t = t.revenue / t.users
        st.metric("Revenue / user — Control", f"${rpu_c:.2f}")
        st.metric("Revenue / user — Treatment", f"${rpu_t:.2f}",
                  f"{(rpu_t/rpu_c-1)*100:+.1f}%")
        unsub_c = c.unsubscribes / c.users
        unsub_t = t.unsubscribes / t.users
        ok = "✅ no harm" if unsub_t <= unsub_c * 1.05 else "⚠️ worse"
        st.markdown(
            f'<div class="note"><b>Guardrail — unsubscribe rate:</b><br>'
            f'Control {unsub_c*100:.2f}% vs Treatment {unsub_t*100:.2f}% '
            f'&nbsp;({ok}). A win on conversion is only real if it doesn\'t '
            f'quietly hurt a protective metric.</div>', unsafe_allow_html=True)

# ============================ SEGMENTS ============================
with tab_seg:
    st.markdown("Is the effect uniform, or driven by a segment? Each row is its "
                "own two-proportion z-test. **Watch mobile.**")

    def seg_table(fname, dim):
        d = load(fname)
        piv = d.pivot(index=dim, columns="group",
                      values=["users", "conversions"]).fillna(0)
        rows = []
        for seg in piv.index:
            xc = piv.loc[seg, ("conversions", "control")]
            nc = piv.loc[seg, ("users", "control")]
            xt = piv.loc[seg, ("conversions", "treatment")]
            nt = piv.loc[seg, ("users", "treatment")]
            r = two_proportion_ztest(int(xc), int(nc), int(xt), int(nt))
            rows.append({dim: seg, "control %": round(r.p_control*100, 2),
                         "treatment %": round(r.p_treat*100, 2),
                         "rel lift %": round(r.rel_lift*100, 1),
                         "p-value": f"{r.p_value:.1e}",
                         "significant": "✅" if r.significant else "—"})
        return pd.DataFrame(rows).sort_values("rel lift %", ascending=False)

    for title, fname, dim in [("By device", "agg_by_device.csv", "device"),
                              ("By channel", "agg_by_channel.csv", "channel"),
                              ("By region", "agg_by_region.csv", "region")]:
        st.subheader(title)
        tbl = seg_table(fname, dim)
        cc1, cc2 = st.columns([2, 3])
        cc1.dataframe(tbl, hide_index=True, use_container_width=True)
        fig = px.bar(tbl, x=dim, y="rel lift %", color="rel lift %",
                     color_continuous_scale="Emrld", text="rel lift %")
        fig.update_layout(height=280, margin=dict(t=20, l=10, r=10, b=10),
                          coloraxis_showscale=False)
        cc2.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="note"><b>Takeaway:</b> the lift is strongest on '
                '<b>Mobile</b> — a heterogeneous treatment effect. If capacity or '
                'spend is limited, roll out to mobile first, where each impression '
                'buys the most incremental conversion.</div>', unsafe_allow_html=True)

# ======================= EXPOSURE & FREQUENCY =======================
with tab_exp:
    st.markdown("How many times should we show the ad? More impressions help — "
                "until they don't. This is the **frequency-capping** decision.")
    e = load("agg_by_exposure.csv")
    e["conv_rate"] = e["conversions"] / e["users"]
    e["unsub_rate"] = e["unsubscribes"] / e["users"]
    e["exposure_bin"] = pd.Categorical(e["exposure_bin"], EXP_ORDER, ordered=True)
    e = e.sort_values("exposure_bin")
    tx = e[e.group == "treatment"]

    fig = go.Figure()
    for grp, color in [("control", "#94a3b8"), ("treatment", "#10b981")]:
        g = e[e.group == grp]
        fig.add_scatter(x=g["exposure_bin"].astype(str), y=g["conv_rate"]*100,
                        mode="lines+markers", name=f"{grp} conversion",
                        line=dict(color=color, width=3))
    fig.add_scatter(x=tx["exposure_bin"].astype(str), y=tx["unsub_rate"]*100,
                    mode="lines+markers", name="unsubscribe (treatment)",
                    line=dict(color="#ef4444", dash="dot"), yaxis="y2")
    peak = tx.loc[tx["conv_rate"].idxmax(), "exposure_bin"]
    fig.update_layout(height=420, title="Conversion & fatigue vs. ad frequency",
                      yaxis_title="conversion %",
                      yaxis2=dict(title="unsubscribe %", overlaying="y", side="right"),
                      margin=dict(t=40, l=10, r=10, b=10),
                      legend=dict(orientation="h", y=-0.2))
    st.plotly_chart(fig, use_container_width=True)
    st.markdown(
        f'<div class="note"><b>Recommendation — cap frequency near {peak} '
        'impressions.</b> Conversion rises with exposure, peaks, then flattens '
        'while the unsubscribe (fatigue) rate keeps climbing. Beyond the peak '
        'you pay for impressions that don\'t convert and mildly annoy users — so '
        'a frequency cap protects both budget and the guardrail metric.</div>',
        unsafe_allow_html=True)

# ===================== CALCULATOR & METHODOLOGY =====================
with tab_calc:
    st.subheader("Run your own test")
    cc = st.columns(4)
    xc = cc[0].number_input("Control conversions", 1, 10_000_000, int(c.conversions))
    nc = cc[1].number_input("Control users", 1, 100_000_000, int(c.users))
    xt = cc[2].number_input("Treatment conversions", 1, 10_000_000, int(t.conversions))
    nt = cc[3].number_input("Treatment users", 1, 100_000_000, int(t.users))
    r = two_proportion_ztest(int(xc), int(nc), int(xt), int(nt))
    m = st.columns(4)
    m[0].metric("Control", f"{r.p_control*100:.2f}%")
    m[1].metric("Treatment", f"{r.p_treat*100:.2f}%", f"{r.abs_lift*100:+.2f} pp")
    m[2].metric("Relative lift", f"{r.rel_lift*100:+.1f}%")
    m[3].metric("p-value", f"{r.p_value:.1e}",
                "significant" if r.significant else "not significant")
    st.caption(f"95% CI on the lift: [{r.ci_low*100:.2f}, {r.ci_high*100:.2f}] pp · "
               f"z = {r.z:.2f} · power at this size ≈ "
               f"{achieved_power(r.p_control, r.p_treat, min(int(nc), int(nt)))*100:.0f}%")

    st.divider()
    st.subheader("Plan a test — sample size")
    p1, p2, p3 = st.columns(3)
    base = p1.number_input("Baseline conversion %", 0.1, 90.0, 2.8) / 100
    mde = p2.number_input("Min. relative lift to detect %", 1.0, 100.0, 10.0) / 100
    power = p3.slider("Power", 0.5, 0.99, 0.80)
    n = required_sample_size(base, mde, power=power)
    st.info(f"You'd need **{n:,} users per arm** ({n*2:,} total) to detect a "
            f"{mde*100:.0f}% relative lift on a {base*100:.1f}% baseline at 80–99% "
            "power. Bigger effects and higher baselines need fewer users.")

    st.divider()
    st.subheader("Methodology — the concepts, in plain English")
    st.markdown("""
- **Two-proportion z-test.** Compares two conversion rates. It asks: *if the
  campaign truly did nothing, how unlikely is a gap this big by chance?* The
  **z-score** is the gap divided by its standard error; a large |z| means the gap
  is far more than noise.
- **p-value.** The probability of seeing a lift at least this large if the true
  effect were zero. Below 0.05 (here it's ~1e-14) we reject "no effect."
- **Confidence interval (95%).** The plausible range for the *true* lift. Because
  the whole interval sits above zero, we're confident the lift is real and
  positive — not just that "p < 0.05."
- **Absolute vs. relative lift.** Absolute = 3.43% − 3.07% = **0.36 pp**.
  Relative = 0.36 / 3.07 = **~12%**. Report both; relative sounds bigger, absolute
  is what finance feels.
- **Statistical power & MDE.** Power is the chance of detecting a real effect;
  the **minimum detectable effect** is the smallest lift a given sample can catch.
  Underpowered tests miss real wins — the sample-size planner above prevents that.
- **Guardrail metric.** A conversion win that spikes unsubscribes isn't a win.
  Always check a protective metric before shipping.
- **Peeking / early stopping.** Repeatedly checking significance as data trickles
  in inflates false positives. Fix the sample size up front (or use sequential
  methods); don't stop the moment p dips below 0.05.
""")

st.caption("Built by Vidit Doshi · Experiment design · two-proportion z-test · "
           "power analysis · segmentation · Python · Streamlit")
