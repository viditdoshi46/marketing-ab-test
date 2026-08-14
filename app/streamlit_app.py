"""
Marketing A/B Test — Experiment Readout.

A decision memo, not a dashboard: it opens with the ship/no-ship verdict, proves
the win with a confidence-interval number-line, then answers "for whom?" and
"how often?". The A/B calculator and sample-size planner live in the sidebar
toolbox. New ad creative (treatment) vs. existing (control), ~600k users.

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

st.set_page_config(page_title="A/B Test Readout | Vidit Doshi",
                   layout="centered", page_icon="🧪")

st.markdown("""
<style>
  .block-container {max-width: 860px; padding-top: 2.2rem;}
  .eyebrow {font-size:.78rem; font-weight:700; letter-spacing:.14em;
            text-transform:uppercase; color:#059669;}
  h1.rt {font-size:1.7rem; font-weight:800; margin:.2rem 0 0; color:#0f172a; letter-spacing:-.02em;}
  .rt-sub {color:#64748b; margin:.3rem 0 1.1rem;}
  /* verdict banner */
  .verdict {border-radius:16px; padding:22px 26px; margin:6px 0 22px;
            background:linear-gradient(120deg,#065f46 0%,#10b981 100%); color:#fff;}
  .verdict .tag {font-size:.8rem; font-weight:700; letter-spacing:.1em; opacity:.9;}
  .verdict .big {font-size:1.5rem; font-weight:800; margin:4px 0 6px;}
  .verdict .exp {font-size:1.0rem; color:#ecfdf5;}
  /* custom stat cards (not st.metric) */
  .strip {display:flex; gap:12px; margin:2px 0 10px;}
  .scard {flex:1; background:#fff; border:1px solid #e5e7eb; border-radius:14px;
          padding:14px 16px; text-align:center;}
  .scard .v {font-size:1.5rem; font-weight:800; color:#0f172a; line-height:1.1;}
  .scard .l {font-size:.74rem; color:#64748b; text-transform:uppercase;
             letter-spacing:.03em; margin-top:3px;}
  .scard .s {font-size:.8rem; color:#059669; font-weight:600; margin-top:2px;}
  .sec {font-size:1.15rem; font-weight:700; color:#0f172a; margin:26px 0 2px;}
  .sec-q {color:#64748b; margin:0 0 10px;}
  .pill {display:inline-block; background:#ecfdf5; color:#065f46; font-weight:600;
         border-radius:999px; padding:3px 12px; font-size:.85rem;}
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

# ---------------- header ----------------
st.markdown('<div class="eyebrow">Experiment Readout</div>'
            '<h1 class="rt">New Ad Creative — Conversion Lift Test</h1>'
            '<div class="rt-sub">Randomized A/B test · ~600,000 users · '
            'treatment (new creative) vs. control (existing)</div>',
            unsafe_allow_html=True)

# ---------------- verdict ----------------
st.markdown(f"""
<div class="verdict">
  <div class="tag">DECISION</div>
  <div class="big">✅ Ship the new creative — roll out to mobile first.</div>
  <div class="exp">It lifted conversion from {res.p_control*100:.2f}% to
     {res.p_treat*100:.2f}% (<b>+{res.rel_lift*100:.1f}%</b>), statistically
     significant at p = {res.p_value:.1e}. The lift is largest on mobile, and the
     unsubscribe guardrail held.</div>
</div>
""", unsafe_allow_html=True)

# ---------------- stat strip (custom cards) ----------------
st.markdown(f"""
<div class="strip">
  <div class="scard"><div class="v">{res.p_control*100:.2f}%</div>
     <div class="l">Control</div></div>
  <div class="scard"><div class="v">{res.p_treat*100:.2f}%</div>
     <div class="l">Treatment</div><div class="s">+{res.abs_lift*100:.2f} pp</div></div>
  <div class="scard"><div class="v">+{res.rel_lift*100:.1f}%</div>
     <div class="l">Relative lift</div></div>
  <div class="scard"><div class="v">{res.p_value:.0e}</div>
     <div class="l">p-value</div><div class="s">significant</div></div>
</div>
""", unsafe_allow_html=True)

# ---------------- is the win real? (CI number-line) ----------------
st.markdown('<div class="sec">Is the win real?</div>'
            '<div class="sec-q">The 95% confidence interval for the true lift — '
            'if it clears zero, the effect is real, not noise.</div>',
            unsafe_allow_html=True)
lo, hi, pt = res.ci_low*100, res.ci_high*100, res.abs_lift*100
fig = go.Figure()
fig.add_shape(type="line", x0=lo, x1=hi, y0=0, y1=0,
              line=dict(color="#10b981", width=8))
fig.add_trace(go.Scatter(x=[pt], y=[0], mode="markers+text",
                         marker=dict(size=16, color="#065f46"),
                         text=[f"+{pt:.2f} pp"], textposition="top center"))
fig.add_vline(x=0, line_dash="dash", line_color="#ef4444",
              annotation_text="no effect", annotation_position="bottom")
fig.update_layout(height=150, margin=dict(t=30, l=10, r=10, b=10),
                  xaxis_title="lift (percentage points)",
                  yaxis=dict(visible=False, range=[-1, 1]),
                  xaxis=dict(range=[min(-0.05, lo-0.1), hi+0.1]))
st.plotly_chart(fig, use_container_width=True)
st.markdown(f'<span class="pill">z = {res.z:.1f} &nbsp;·&nbsp; CI '
            f'[{lo:.2f}, {hi:.2f}] pp &nbsp;·&nbsp; entirely above zero</span>',
            unsafe_allow_html=True)

# ---------------- who responded most? ----------------
st.markdown('<div class="sec">Who responded most?</div>'
            '<div class="sec-q">A separate z-test per segment. The effect is '
            'heterogeneous — mobile drives it.</div>', unsafe_allow_html=True)


def seg(fname, dim):
    d = load(fname).pivot(index=dim, columns="group",
                          values=["users", "conversions"]).fillna(0)
    out = []
    for s in d.index:
        r = two_proportion_ztest(int(d.loc[s, ("conversions", "control")]),
                                 int(d.loc[s, ("users", "control")]),
                                 int(d.loc[s, ("conversions", "treatment")]),
                                 int(d.loc[s, ("users", "treatment")]))
        out.append({dim: s, "rel_lift": r.rel_lift*100,
                    "sig": "✅" if r.significant else "—"})
    return pd.DataFrame(out).sort_values("rel_lift", ascending=False)

dev = seg("agg_by_device.csv", "device")
figd = px.bar(dev.sort_values("rel_lift"), x="rel_lift", y="device",
              orientation="h", text=dev.sort_values("rel_lift")["rel_lift"].round(1),
              color="rel_lift", color_continuous_scale="Emrld")
figd.update_layout(height=220, coloraxis_showscale=False,
                   xaxis_title="relative lift %", margin=dict(t=10, l=10, r=10, b=10))
st.plotly_chart(figd, use_container_width=True)
with st.expander("By channel & region"):
    cc1, cc2 = st.columns(2)
    cc1.dataframe(seg("agg_by_channel.csv", "channel"), hide_index=True, use_container_width=True)
    cc2.dataframe(seg("agg_by_region.csv", "region"), hide_index=True, use_container_width=True)

# ---------------- how often? ----------------
st.markdown('<div class="sec">How often should we show it?</div>'
            '<div class="sec-q">Conversion rises with frequency, then fatigues — '
            'so there\'s an optimal cap.</div>', unsafe_allow_html=True)
e = load("agg_by_exposure.csv")
e["conv"] = e.conversions/e.users*100
e["unsub"] = e.unsubscribes/e.users*100
e["exposure_bin"] = pd.Categorical(e.exposure_bin, EXP_ORDER, ordered=True)
e = e.sort_values("exposure_bin")
tx = e[e.group == "treatment"]
figf = go.Figure()
figf.add_scatter(x=tx.exposure_bin.astype(str), y=tx.conv, mode="lines+markers",
                 name="conversion", line=dict(color="#10b981", width=3))
figf.add_scatter(x=tx.exposure_bin.astype(str), y=tx.unsub, mode="lines+markers",
                 name="unsubscribe (fatigue)", line=dict(color="#ef4444", dash="dot"),
                 yaxis="y2")
peak = tx.loc[tx.conv.idxmax(), "exposure_bin"]
figf.update_layout(height=320, margin=dict(t=10, l=10, r=10, b=10),
                   yaxis_title="conversion %",
                   yaxis2=dict(title="unsubscribe %", overlaying="y", side="right"),
                   legend=dict(orientation="h", y=-0.25))
st.plotly_chart(figf, use_container_width=True)
st.markdown(f'<span class="pill">Recommended frequency cap ≈ {peak} impressions'
            '</span>', unsafe_allow_html=True)

with st.expander("📚 Methodology — the statistics in plain English"):
    st.markdown("""
- **Two-proportion z-test** compares two rates: the z-score is the gap ÷ its
  standard error; large |z| means the gap is far more than sampling noise.
- **p-value** = probability of a lift this big if the true effect were zero
  (here ~1e-14 → reject "no effect"). It is *not* the probability the null is true.
- **Confidence interval** = the plausible range for the true lift; above zero ⇒ a
  real, positive effect (more informative than a bare p-value).
- **Power & MDE** (sidebar planner): power is the chance of catching a real effect;
  the minimum detectable effect is the smallest lift a sample can find.
- **Guardrail metric**: a conversion win that spikes unsubscribes isn't a win.
- **Peeking**: repeatedly checking significance inflates false positives — fix the
  sample size up front.
""")

# ================= SIDEBAR TOOLBOX =================
with st.sidebar:
    st.header("🧮 Test toolbox")
    st.caption("Run any two-arm test, or plan the next one.")
    st.subheader("A/B calculator")
    xc = st.number_input("Control conversions", 1, 10_000_000, int(c.conversions))
    nc = st.number_input("Control users", 1, 100_000_000, int(c.users))
    xt = st.number_input("Treatment conversions", 1, 10_000_000, int(t.conversions))
    nt = st.number_input("Treatment users", 1, 100_000_000, int(t.users))
    r = two_proportion_ztest(int(xc), int(nc), int(xt), int(nt))
    st.metric("Relative lift", f"{r.rel_lift*100:+.1f}%", f"{r.abs_lift*100:+.2f} pp")
    st.metric("p-value", f"{r.p_value:.1e}",
              "significant" if r.significant else "not significant")
    st.caption(f"95% CI [{r.ci_low*100:.2f}, {r.ci_high*100:.2f}] pp · "
               f"power ≈ {achieved_power(r.p_control, r.p_treat, min(int(nc), int(nt)))*100:.0f}%")
    st.divider()
    st.subheader("Sample-size planner")
    base = st.number_input("Baseline %", 0.1, 90.0, 2.8) / 100
    mde = st.number_input("Min. relative lift %", 1.0, 100.0, 10.0) / 100
    power = st.slider("Power", 0.5, 0.99, 0.80)
    n = required_sample_size(base, mde, power=power)
    st.info(f"**{n:,} users / arm** to detect a {mde*100:.0f}% lift on a "
            f"{base*100:.1f}% baseline.")
    st.caption("Built by Vidit Doshi · experiment design · Python · Streamlit")
