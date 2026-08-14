"""
Small, dependency-free statistics for the A/B test (uses the standard library's
NormalDist, so no scipy needed). Everything an analyst should be able to defend:
a two-proportion z-test, a confidence interval on the lift, statistical power,
and the sample size needed to detect a given effect.
"""
from __future__ import annotations
from dataclasses import dataclass
from math import sqrt
from statistics import NormalDist

Z = NormalDist()          # standard normal


@dataclass
class ABResult:
    p_control: float
    p_treat: float
    abs_lift: float          # p_treat - p_control (percentage points, as a proportion)
    rel_lift: float          # abs_lift / p_control
    z: float
    p_value: float           # two-sided
    ci_low: float            # 95% CI on the absolute lift
    ci_high: float
    significant: bool


def two_proportion_ztest(x_c, n_c, x_t, n_t, alpha=0.05) -> ABResult:
    """x_* = conversions, n_* = users. Pooled SE for the test; unpooled for the CI."""
    p_c, p_t = x_c / n_c, x_t / n_t
    diff = p_t - p_c
    p_pool = (x_c + x_t) / (n_c + n_t)
    se_pool = sqrt(p_pool * (1 - p_pool) * (1 / n_c + 1 / n_t))
    z = diff / se_pool if se_pool > 0 else 0.0
    p_value = 2 * (1 - Z.cdf(abs(z)))
    se_unpool = sqrt(p_c * (1 - p_c) / n_c + p_t * (1 - p_t) / n_t)
    zc = Z.inv_cdf(1 - alpha / 2)
    return ABResult(p_c, p_t, diff, diff / p_c if p_c else 0.0, z, p_value,
                    diff - zc * se_unpool, diff + zc * se_unpool, p_value < alpha)


def required_sample_size(p_base, mde_rel, alpha=0.05, power=0.80) -> int:
    """Users PER ARM to detect a relative lift `mde_rel` on a base rate `p_base`."""
    p1 = p_base
    p2 = p_base * (1 + mde_rel)
    z_a = Z.inv_cdf(1 - alpha / 2)
    z_b = Z.inv_cdf(power)
    pbar = (p1 + p2) / 2
    num = (z_a * sqrt(2 * pbar * (1 - pbar)) + z_b * sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2
    return int(num / (p2 - p1) ** 2) + 1


def achieved_power(p_c, p_t, n_per_arm, alpha=0.05) -> float:
    """Probability of detecting the observed effect at this sample size."""
    diff = abs(p_t - p_c)
    se = sqrt(p_c * (1 - p_c) / n_per_arm + p_t * (1 - p_t) / n_per_arm)
    if se == 0:
        return 1.0
    z_a = Z.inv_cdf(1 - alpha / 2)
    return 1 - Z.cdf(z_a - diff / se)
