"""Reusable intelligence analysis utilities."""
from __future__ import annotations

from datetime import datetime
from typing import Any

import numpy as np


def detect_anomaly(values: list[float], threshold: float = 3.0) -> list[int]:
    """Return indices of anomalous values using modified Z-score."""
    if len(values) < 3:
        return []
    median = np.median(values)
    mad = np.median([abs(v - median) for v in values]) or 1e-9
    modified_z_scores = [0.6745 * (v - median) / mad for v in values]
    return [i for i, z in enumerate(modified_z_scores) if abs(z) > threshold]


def simple_forecast(values: list[float], periods: int = 7) -> list[float]:
    """Simple trend + seasonality forecast."""
    if len(values) < 7:
        avg = sum(values) / len(values) if values else 0
        return [avg] * periods

    # Simple linear trend
    n = len(values)
    x = list(range(n))
    x_mean = sum(x) / n
    y_mean = sum(values) / n
    slope = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n)) / sum((xi - x_mean) ** 2 for xi in x)
    intercept = y_mean - slope * x_mean

    # Weekly seasonality (if enough data)
    if n >= 14:
        seasonal = []
        for day in range(7):
            day_values = [values[i] for i in range(day, n, 7)]
            seasonal.append(sum(day_values) / len(day_values) if day_values else y_mean)
        seasonal_avg = sum(seasonal) / len(seasonal)
        seasonal_factors = [s / seasonal_avg for s in seasonal]
    else:
        seasonal_factors = [1.0] * 7

    forecasts = []
    for i in range(periods):
        trend = intercept + slope * (n + i)
        season = seasonal_factors[(n + i) % 7]
        forecasts.append(max(0, trend * season))

    return forecasts


def calculate_cohorts(orders: list[dict[str, Any]]) -> dict[str, Any]:
    """Calculate cohort retention from orders."""
    if not orders:
        return {}

    # Group by customer first order month
    customer_first_order: dict[str, str] = {}
    customer_orders: dict[str, list[datetime]] = {}

    for order in orders:
        customer_id = str(order.get("customer_id", ""))
        order_date = order.get("created_at")
        if not customer_id or not order_date:
            continue
        if isinstance(order_date, str):
            order_date = datetime.fromisoformat(order_date.replace("Z", "+00:00"))

        if customer_id not in customer_orders:
            customer_orders[customer_id] = []
        customer_orders[customer_id].append(order_date)

    for cid, dates in customer_orders.items():
        first = min(dates)
        customer_first_order[cid] = first.strftime("%Y-%m")

    # Build cohort table
    cohorts: dict[str, dict[str, set[str]]] = {}
    for cid, first_month in customer_first_order.items():
        if first_month not in cohorts:
            cohorts[first_month] = {}
        for order_date in customer_orders[cid]:
            order_date.strftime("%Y-%m")
            months_diff = (order_date.year - datetime.strptime(first_month, "%Y-%m").year) * 12 + \
                         (order_date.month - datetime.strptime(first_month, "%Y-%m").month)
            period_key = f"M{months_diff}"
            if period_key not in cohorts[first_month]:
                cohorts[first_month][period_key] = set()
            cohorts[first_month][period_key].add(cid)

    # Calculate retention percentages
    result = {}
    for cohort_month, periods in sorted(cohorts.items()):
        cohort_size = len(periods.get("M0", set()))
        if cohort_size == 0:
            continue
        result[cohort_month] = {
            "size": cohort_size,
            "retention": {
                period: round(len(customers) / cohort_size * 100, 1)
                for period, customers in sorted(periods.items())
            }
        }

    return result


def calculate_rfm(
    orders: list[dict[str, Any]],
    now: datetime | None = None,
) -> dict[str, dict[str, Any]]:
    """Calculate RFM scores for customers."""
    now = now or datetime.utcnow()

    customer_data: dict[str, dict[str, Any]] = {}
    for order in orders:
        cid = str(order.get("customer_id", ""))
        amount = float(order.get("total_price", 0) or 0)
        date = order.get("created_at")
        if not cid or not date:
            continue
        if isinstance(date, str):
            date = datetime.fromisoformat(date.replace("Z", "+00:00"))

        if cid not in customer_data:
            customer_data[cid] = {"orders": 0, "total": 0.0, "last_order": date}
        customer_data[cid]["orders"] += 1
        customer_data[cid]["total"] += amount
        if date > customer_data[cid]["last_order"]:
            customer_data[cid]["last_order"] = date

    # Calculate scores (1-5)
    recencies = [(now - d["last_order"]).days for d in customer_data.values()]
    frequencies = [d["orders"] for d in customer_data.values()]
    monetary = [d["total"] for d in customer_data.values()]

    def score(values: list[float], value: float, reverse: bool = False) -> int:
        if not values:
            return 3
        sorted_vals = sorted(values, reverse=reverse)
        idx = sorted_vals.index(value) if value in sorted_vals else len(sorted_vals) // 2
        return min(5, max(1, int(idx / len(sorted_vals) * 5) + 1))

    results = {}
    for cid, data in customer_data.items():
        recency_days = (now - data["last_order"]).days
        r = score(recencies, recency_days, reverse=True)  # Lower recency = higher score
        f = score(frequencies, data["orders"])
        m = score(monetary, data["total"])

        # Segment classification
        if r >= 4 and f >= 4 and m >= 4:
            segment = "champions"
        elif r >= 3 and f >= 3 and m >= 3:
            segment = "loyal"
        elif r >= 4 and f <= 2:
            segment = "new"
        elif r <= 2 and f >= 3:
            segment = "at_risk"
        elif r <= 2 and f <= 2 and m >= 3:
            segment = "hibernating"
        else:
            segment = "needs_attention"

        results[cid] = {
            "recency_days": recency_days,
            "frequency": data["orders"],
            "monetary": round(data["total"], 2),
            "r": r,
            "f": f,
            "m": m,
            "segment": segment,
        }

    return results
