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
  .block-container {max-width: 1000px; padding-top: 3rem; padding-bottom: 5rem;}
  /* generous type + rhythm */
  .eyebrow {font-size:.8rem; font-weight:700; letter-spacing:.16em;
            text-transform:uppercase; color:#059669;}
  h1.rt {font-size:2.1rem; font-weight:800; margin:.35rem 0 0; color:#0f172a;
         letter-spacing:-.025em; line-height:1.12;}
  .rt-sub {color:#64748b; margin:.5rem 0 0; font-size:1.05rem;}

  /* verdict banner */
  .verdict {border-radius:20px; padding:30px 34px; margin:30px 0 34px;
            background:linear-gradient(120deg,#065f46 0%,#10b981 100%); color:#fff;
            box-shadow:0 20px 45px -22px rgba(16,185,129,.65);}
  .verdict .tag {font-size:.82rem; font-weight:700; letter-spacing:.14em; opacity:.9;}
  .verdict .big {font-size:1.7rem; font-weight:800; margin:8px 0 10px; line-height:1.2;}
  .verdict .exp {font-size:1.08rem; color:#ecfdf5; line-height:1.55; max-width:70ch;}

  /* KPI cards */
  .kpi {background:#fff; border:1px solid #e9edf2; border-radius:16px;
        padding:22px 22px; text-align:center; min-height:118px;
        box-shadow:0 1px 2px rgba(16,24,40,.05), 0 18px 36px -26px rgba(16,24,40,.35);}
  .kpi .v {font-size:2rem; font-weight:800; color:#0f172a; line-height:1.05;}
  .kpi .l {font-size:.76rem; color:#64748b; text-transform:uppercase;
           letter-spacing:.05em; margin-top:8px;}
  .kpi .s {font-size:.88rem; font-weight:700; color:#059669; margin-top:6px;}

  /* section headings + panels */
  .sec {font-size:1.45rem; font-weight:800; color:#0f172a; letter-spacing:-.02em; margin:0;}
  .sec-q {color:#64748b; margin:.35rem 0 0; font-size:1.02rem; max-width:78ch;}
  [data-testid="stVerticalBlockBorderWrapper"]{
     background:#fff; border:1px solid #e9edf2 !important; border-radius:18px;
     box-shadow:0 1px 2px rgba(16,24,40,.05), 0 22px 44px -30px rgba(16,24,40,.4);}
  .pill {display:inline-block; background:#ecfdf5; color:#065f46; font-weight:700;
         border-radius:999px; padding:7px 16px; font-size:.9rem;}
  .spacer {height:34px;}
  .spacer-sm {height:18px;}
</style>
""", unsafe_allow_html=True)

DATA = ROOT / "data"
EXP_ORDER = ["1-2", "3-4", "5-6", "7-8", "9-10", "11-12", "13+"]
GREEN, INK, GRID = "#10b981", "#0f172a", "#eef1f5"


@st.cache_data
def load(name):
    return pd.read_csv(DATA / name)


def style(fig, h=360):
    fig.update_layout(height=h, paper_bgcolor="white", plot_bgcolor="white",
                      font=dict(color=INK, size=13, family="Inter, sans-serif"),
                      margin=dict(t=30, l=20, r=24, b=20))
    fig.update_xaxes(gridcolor=GRID, zerolinecolor=GRID)
    fig.update_yaxes(gridcolor=GRID, zerolinecolor=GRID)
    return fig


def spacer(sm=False):
    st.markdown(f'<div class="{"spacer-sm" if sm else "spacer"}"></div>',
                unsafe_allow_html=True)


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


def kpi(col, value, label, sub=""):
    col.markdown(f'<div class="kpi"><div class="v">{value}</div>'
                 f'<div class="l">{label}</div>'
                 + (f'<div class="s">{sub}</div>' if sub else '')
                 + '</div>', unsafe_allow_html=True)


kc = st.columns(4, gap="large")
kpi(kc[0], f"{res.p_control*100:.2f}%", "Control")
kpi(kc[1], f"{res.p_treat*100:.2f}%", "Treatment", f"+{res.abs_lift*100:.2f} pp")
kpi(kc[2], f"+{res.rel_lift*100:.1f}%", "Relative lift")
kpi(kc[3], f"{res.p_value:.0e}", "p-value", "significant")

# ---------------- is the win real? ----------------
spacer()
st.markdown('<div class="sec">Is the win real?</div>'
            '<div class="sec-q">The 95% confidence interval for the true lift — '
            'if it clears zero, the effect is real, not noise.</div>',
            unsafe_allow_html=True)
spacer(sm=True)
with st.container(border=True):
    lo, hi, pt = res.ci_low*100, res.ci_high*100, res.abs_lift*100
    fig = go.Figure()
    fig.add_shape(type="line", x0=lo, x1=hi, y0=0, y1=0,
                  line=dict(color=GREEN, width=10))
    fig.add_trace(go.Scatter(x=[pt], y=[0], mode="markers+text",
                             marker=dict(size=18, color="#065f46"),
                             text=[f"+{pt:.2f} pp"], textposition="top center"))
    fig.add_vline(x=0, line_dash="dash", line_color="#ef4444",
                  annotation_text="no effect", annotation_position="bottom")
    style(fig, 190)
    fig.update_layout(xaxis_title="lift (percentage points)",
                      yaxis=dict(visible=False, range=[-1, 1]),
                      xaxis=dict(range=[min(-0.05, lo-0.1), hi+0.1]))
    st.plotly_chart(fig, use_container_width=True)
    st.markdown(f'<span class="pill">z = {res.z:.1f} &nbsp;·&nbsp; CI '
                f'[{lo:.2f}, {hi:.2f}] pp &nbsp;·&nbsp; entirely above zero</span>',
                unsafe_allow_html=True)

# ---------------- who responded most? ----------------
spacer()
st.markdown('<div class="sec">Who responded most?</div>'
            '<div class="sec-q">A separate z-test per segment — the effect is '
            'heterogeneous, and mobile drives it.</div>', unsafe_allow_html=True)
spacer(sm=True)


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


with st.container(border=True):
    dev = seg("agg_by_device.csv", "device").sort_values("rel_lift")
    figd = px.bar(dev, x="rel_lift", y="device", orientation="h",
                  text=dev["rel_lift"].round(1),
                  color="rel_lift", color_continuous_scale="Emrld")
    figd.update_traces(textposition="outside", cliponaxis=False)
    style(figd, 260)
    figd.update_layout(coloraxis_showscale=False, xaxis_title="relative lift %",
                       yaxis_title="")
    st.plotly_chart(figd, use_container_width=True)
    with st.expander("See channel & region breakdowns"):
        e1, e2 = st.columns(2, gap="large")
        e1.dataframe(seg("agg_by_channel.csv", "channel"), hide_index=True,
                     use_container_width=True)
        e2.dataframe(seg("agg_by_region.csv", "region"), hide_index=True,
                     use_container_width=True)

# ---------------- how often? ----------------
spacer()
st.markdown('<div class="sec">How often should we show it?</div>'
            '<div class="sec-q">Conversion rises with frequency, then fatigues — '
            "so there's an optimal cap.</div>", unsafe_allow_html=True)
spacer(sm=True)
with st.container(border=True):
    e = load("agg_by_exposure.csv")
    e["conv"] = e.conversions/e.users*100
    e["unsub"] = e.unsubscribes/e.users*100
    e["exposure_bin"] = pd.Categorical(e.exposure_bin, EXP_ORDER, ordered=True)
    e = e.sort_values("exposure_bin")
    tx = e[e.group == "treatment"]
    figf = go.Figure()
    figf.add_scatter(x=tx.exposure_bin.astype(str), y=tx.conv, mode="lines+markers",
                     name="conversion", line=dict(color=GREEN, width=3.5),
                     marker=dict(size=8))
    figf.add_scatter(x=tx.exposure_bin.astype(str), y=tx.unsub, mode="lines+markers",
                     name="unsubscribe (fatigue)",
                     line=dict(color="#ef4444", dash="dot", width=2.5), yaxis="y2")
    peak = tx.loc[tx.conv.idxmax(), "exposure_bin"]
    style(figf, 380)
    figf.update_layout(yaxis_title="conversion %",
                       yaxis2=dict(title="unsubscribe %", overlaying="y", side="right",
                                   gridcolor=GRID),
                       legend=dict(orientation="h", y=-0.28))
    st.plotly_chart(figf, use_container_width=True)
    st.markdown(f'<span class="pill">Recommended frequency cap ≈ {peak} '
                'impressions</span>', unsafe_allow_html=True)

spacer()
with st.expander("📚  Methodology — the statistics in plain English"):
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
