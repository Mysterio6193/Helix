"""Statistical significance calculator for A/B tests.

Implements:
- Chi-square test for conversion rates (proportions)
- T-test for continuous metrics (revenue, time on site)
- Bayesian bandit for dynamic allocation (optional)
"""
from __future__ import annotations

import math
from typing import Any


def chi_square_test(
    successes_a: int,
    trials_a: int,
    successes_b: int,
    trials_b: int,
) -> dict[str, Any]:
    """Chi-square test of independence for conversion rates.

    Returns p-value, confidence level, and whether the difference is significant.
    """
    if trials_a == 0 or trials_b == 0:
        return {"p_value": 1.0, "significant": False, "uplift": 0.0}

    rate_a = successes_a / trials_a
    rate_b = successes_b / trials_b

    # Pooled probability
    total_successes = successes_a + successes_b
    total_trials = trials_a + trials_b
    pooled_rate = total_successes / total_trials if total_trials > 0 else 0

    # Expected values
    expected_a_success = trials_a * pooled_rate
    expected_a_fail = trials_a * (1 - pooled_rate)
    expected_b_success = trials_b * pooled_rate
    expected_b_fail = trials_b * (1 - pooled_rate)

    # Chi-square statistic
    chi2 = 0.0
    obs = [
        (successes_a, expected_a_success),
        (trials_a - successes_a, expected_a_fail),
        (successes_b, expected_b_success),
        (trials_b - successes_b, expected_b_fail),
    ]
    for observed, expected in obs:
        if expected > 0:
            chi2 += (observed - expected) ** 2 / expected

    # Chi-square with 1 degree of freedom
    # p-value approximation using error function
    p_value = 1 - _chi2_cdf(chi2, 1)

    # Uplift
    if rate_a > 0:
        uplift = (rate_b - rate_a) / rate_a
    else:
        uplift = float('inf') if rate_b > 0 else 0.0

    return {
        "p_value": p_value,
        "significant": p_value < 0.05,
        "confidence": 1 - p_value,
        "uplift": uplift,
        "rate_a": rate_a,
        "rate_b": rate_b,
        "chi2": chi2,
    }


def two_proportion_z_test(
    successes_a: int,
    trials_a: int,
    successes_b: int,
    trials_b: int,
) -> dict[str, Any]:
    """Z-test for two proportions (alternative to chi-square, same result)."""
    if trials_a == 0 or trials_b == 0:
        return {"p_value": 1.0, "significant": False, "uplift": 0.0}

    p_a = successes_a / trials_a
    p_b = successes_b / trials_b

    p_pooled = (successes_a + successes_b) / (trials_a + trials_b)
    se = math.sqrt(p_pooled * (1 - p_pooled) * (1 / trials_a + 1 / trials_b))

    if se == 0:
        return {"p_value": 1.0, "significant": False, "uplift": 0.0}

    z = (p_b - p_a) / se
    p_value = 2 * (1 - _normal_cdf(abs(z)))

    if p_a > 0:
        uplift = (p_b - p_a) / p_a
    else:
        uplift = float('inf') if p_b > 0 else 0.0

    return {
        "p_value": p_value,
        "significant": p_value < 0.05,
        "confidence": 1 - p_value,
        "uplift": uplift,
        "rate_a": p_a,
        "rate_b": p_b,
        "z_score": z,
    }


def welch_t_test(
    mean_a: float,
    std_a: float,
    n_a: int,
    mean_b: float,
    std_b: float,
    n_b: int,
) -> dict[str, Any]:
    """Welch's t-test for continuous metrics (revenue, time, etc.)."""
    if n_a < 2 or n_b < 2:
        return {"p_value": 1.0, "significant": False, "uplift": 0.0}

    # Standard error
    se_a = std_a / math.sqrt(n_a)
    se_b = std_b / math.sqrt(n_b)
    se = math.sqrt(se_a ** 2 + se_b ** 2)

    if se == 0:
        return {"p_value": 1.0, "significant": False, "uplift": 0.0}

    t = (mean_b - mean_a) / se

    # Degrees of freedom (Welch-Satterthwaite)
    numerator = (se_a ** 2 + se_b ** 2) ** 2
    denominator = (se_a ** 4 / (n_a - 1)) + (se_b ** 4 / (n_b - 1))
    df = numerator / denominator if denominator > 0 else n_a + n_b - 2

    # p-value approximation
    p_value = 2 * (1 - _t_cdf(abs(t), df))

    if mean_a > 0:
        uplift = (mean_b - mean_a) / mean_a
    else:
        uplift = float('inf') if mean_b > 0 else 0.0

    return {
        "p_value": p_value,
        "significant": p_value < 0.05,
        "confidence": 1 - p_value,
        "uplift": uplift,
        "mean_a": mean_a,
        "mean_b": mean_b,
        "t_score": t,
        "df": df,
    }


def bonferroni_correction(
    p_values: dict[str, float],
    alpha: float = 0.05,
) -> dict[str, dict[str, float | bool]]:
    """Adjust p-values for multiple comparisons using Bonferroni correction.

    Returns a dict mapping each comparison key to its original p-value,
    adjusted alpha, and whether it remains significant after correction.
    """
    n_comparisons = len(p_values)
    if n_comparisons == 0:
        return {}
    corrected_alpha = alpha / n_comparisons
    return {
        key: {
            "p_value": round(p_val, 4),
            "corrected_alpha": round(corrected_alpha, 4),
            "significant": p_val < corrected_alpha,
            "confidence": round((1 - p_val) * 100, 1),
        }
        for key, p_val in p_values.items()
    }


def pairwise_z_tests(
    variants: dict[str, dict[str, int | float]],
    control_id: str,
    metric_key: str = "conversions",
    denominator_key: str = "impressions",
    alpha: float = 0.05,
) -> dict[str, Any]:
    """Run pairwise two-proportion z-tests for all variants against control,
    with Bonferroni correction for multiple comparisons.

    Returns statistical test results for each variant vs control.
    """
    control = variants.get(control_id)
    if not control:
        return {}

    control_successes = int(control.get(metric_key, 0))
    control_trials = int(control.get(denominator_key, 0))
    if control_trials == 0:
        return {}

    raw_p_values: dict[str, float] = {}
    pairwise_results: dict[str, Any] = {}
    control_rate = control_successes / control_trials

    for vid, vdata in variants.items():
        if vid == control_id:
            continue
        v_successes = int(vdata.get(metric_key, 0))
        v_trials = int(vdata.get(denominator_key, 0))
        if v_trials == 0:
            continue

        test = two_proportion_z_test(
            control_successes, control_trials,
            v_successes, v_trials,
        )
        raw_p_values[vid] = test["p_value"]
        pairwise_results[vid] = test

    # Apply Bonferroni correction
    corrected = bonferroni_correction(raw_p_values, alpha)

    results = {}
    for vid, test in pairwise_results.items():
        corr = corrected.get(vid, {})
        v_rate = variants[vid].get(metric_key, 0) / max(variants[vid].get(denominator_key, 0), 1)
        results[vid] = {
            "p_value": round(test["p_value"], 4),
            "corrected_alpha": corr.get("corrected_alpha", alpha),
            "significant": corr.get("significant", False),
            "confidence": corr.get("confidence", round((1 - test["p_value"]) * 100, 1)),
            "uplift": round((v_rate - control_rate) / control_rate * 100, 1) if control_rate > 0 else 0.0,
            "rate_a": round(control_rate * 100, 2),
            "rate_b": round(v_rate * 100, 2),
            "z_score": test.get("z_score", 0),
        }
    return results


# ─── Distribution functions ───────────────────────────────────────────

def _normal_cdf(x: float) -> float:
    """Cumulative distribution function for standard normal."""
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def _chi2_cdf(x: float, k: int) -> float:
    """Approximate CDF for chi-square distribution."""
    if x < 0:
        return 0.0
    if k == 1:
        return _normal_cdf(math.sqrt(x)) - _normal_cdf(-math.sqrt(x))
    # Gamma approximation for k > 1
    from math import gamma
    return _incomplete_gamma(k / 2, x / 2) / gamma(k / 2)


def _incomplete_gamma(s: float, x: float) -> float:
    """Lower incomplete gamma function approximation."""
    if x < s + 1:
        # Series representation
        result = 0.0
        term = 1.0 / s
        n = 1
        while n < 100:
            result += term
            term *= x / (s + n)
            if term < 1e-10:
                break
            n += 1
        return result * math.exp(-x + s * math.log(x))
    else:
        # Continued fraction
        a = 1.0 - s
        b = x + a + 1.0
        c = 1.0 / 1e-30
        d = 1.0 / b
        h = d
        for _i in range(1, 100):
            a += 1
            b += 2
            d = 1.0 / (b + a * d)
            c = b + a / c
            delta = c * d
            h *= delta
            if abs(delta - 1.0) < 1e-10:
                break
        return math.exp(-x + s * math.log(x)) * h


def _t_cdf(t: float, df: float) -> float:
    """Approximate CDF for t-distribution."""
    if df > 30:
        return _normal_cdf(t)

    x = df / (df + t ** 2)
    a = df / 2
    b = 0.5

    # Incomplete beta approximation
    return 1 - 0.5 * _incomplete_beta(x, a, b)


def _incomplete_beta(x: float, a: float, b: float) -> float:
    """Approximate incomplete beta function."""
    if x == 0:
        return 0.0
    if x == 1:
        return 1.0

    from math import lgamma

    ln_beta = lgamma(a) + lgamma(b) - lgamma(a + b)
    front = math.exp(math.log(x) * a + math.log(1 - x) * b - ln_beta) / a

    f = 1.0
    c = 1.0
    d = 0.0

    for m in range(100):
        if m % 2 == 0:
            num = m * (b - m) * x / ((a + 2 * m - 1) * (a + 2 * m))
        else:
            num = -(a + m) * (a + b + m) * x / ((a + 2 * m) * (a + 2 * m + 1))

        d = 1 + num * d
        if abs(d) < 1e-30:
            d = 1e-30
        c = 1 + num / c
        if abs(c) < 1e-30:
            c = 1e-30
        d = 1 / d
        delta = d * c
        f *= delta
        if abs(delta - 1.0) < 1e-10:
            break

    return front * f
