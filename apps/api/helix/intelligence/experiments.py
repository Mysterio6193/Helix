"""Experiment engine — traffic allocation, event tracking, and statistical evaluation."""
from __future__ import annotations

import hashlib
import itertools
import random
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from helix.core.logging import get_logger
from helix.intelligence.stats import (
    bonferroni_correction,
    two_proportion_z_test,
)
from helix.models.intelligence import Experiment, ExperimentEvent

log = get_logger("helix.intelligence.experiments")


class ExperimentEngine:
    """Engine for managing A/B and multivariate experiments with statistical rigor."""

    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def generate_mvt_variants(factors: dict[str, Any]) -> list[dict[str, Any]]:
        """Generate full-factorial MVT variants from factor definitions.

        factors: {factor_name: {levels: [{value, config?}]}}
        Returns a list of variant dicts with factor-level metadata.
        """
        if not factors:
            return []

        factor_names = list(factors.keys())
        level_lists = []
        for fn in factor_names:
            fdata = factors[fn]
            levels = fdata if isinstance(fdata, list) else fdata.get("levels", [])
            level_lists.append(levels)

        combinations = list(itertools.product(*level_lists))
        variants = []
        for idx, combo in enumerate(combinations):
            vid = f"mvt_{idx}"
            factor_map = {}
            config = {}
            for fn, level in zip(factor_names, combo, strict=False):
                level_value = level if isinstance(level, str) else level.get("value", str(level))
                factor_map[fn] = level_value
                lconfig = level.get("config", {}) if isinstance(level, dict) else {}
                config.update(lconfig)

            variant_name = " / ".join(
                level if isinstance(level, str) else level.get("value", str(level))
                for level in combo
            )

            variants.append({
                "id": vid,
                "name": variant_name,
                "traffic_pct": 100 // max(len(combinations), 1),
                "config": config,
                "factor_levels": factor_map,
            })

        return variants

    @staticmethod
    def compute_factor_analysis(
        results: dict[str, dict[str, Any]],
        factors: dict[str, Any],
        control_id: str | None = None,
    ) -> dict[str, Any]:
        """Analyze MVT results at the factor level.

        For each factor, aggregates all variants sharing a factor level and
        compares them against the control factor level using pairwise z-tests
        with Bonferroni correction.
        """
        if not factors:
            return {}

        factor_analysis = {}
        all_variant_ids = list(results.keys())
        factor_names = list(factors.keys())

        for factor_name in factor_names:
            fdata = factors[factor_name]
            levels = fdata if isinstance(fdata, list) else fdata.get("levels", [])
            level_values = []
            for lev in levels:
                if isinstance(lev, str):
                    level_values.append(lev)
                else:
                    level_values.append(lev.get("value", ""))

            # Group variants by factor level
            level_groups: dict[str, list[str]] = {lv: [] for lv in level_values}
            for vid in all_variant_ids:
                vdata = results.get(vid, {})
                v_levels = vdata.get("factor_levels", {})
                assigned = v_levels.get(factor_name)
                if assigned in level_groups:
                    level_groups[assigned].append(vid)

            # Aggregate metrics per factor level
            level_aggregates: dict[str, dict[str, int | float]] = {}
            for lv, vids in level_groups.items():
                total_impressions = sum(int(results.get(v, {}).get("impressions", 0)) for v in vids)
                total_conversions = sum(int(results.get(v, {}).get("conversions", 0)) for v in vids)
                total_clicks = sum(int(results.get(v, {}).get("clicks", 0)) for v in vids)
                total_revenue = sum(float(results.get(v, {}).get("revenue", 0)) for v in vids)
                level_aggregates[lv] = {
                    "variants": vids,
                    "impressions": total_impressions,
                    "conversions": total_conversions,
                    "clicks": total_clicks,
                    "revenue": total_revenue,
                    "conversion_rate": round(total_conversions / max(total_impressions, 1) * 100, 2),
                }

            if not level_aggregates:
                continue

            # Use first level as control
            control_level = level_values[0] if level_values else None
            if not control_level or control_level not in level_aggregates:
                continue

            control_agg = level_aggregates[control_level]
            control_conv = int(control_agg.get("conversions", 0))
            control_imp = int(control_agg.get("impressions", 0))

            factor_level_results = {}
            raw_p_values = {}
            for lv, agg in level_aggregates.items():
                if lv == control_level:
                    continue
                test = two_proportion_z_test(
                    control_conv, control_imp,
                    int(agg.get("conversions", 0)),
                    int(agg.get("impressions", 0)),
                )
                raw_p_values[lv] = test["p_value"]
                factor_level_results[lv] = test

            corrected = bonferroni_correction(raw_p_values, 0.05)

            analysis_levels = {}
            for lv, test in factor_level_results.items():
                corr = corrected.get(lv, {})
                analysis_levels[lv] = {
                    "p_value": round(test["p_value"], 4),
                    "corrected_alpha": corr.get("corrected_alpha", 0.05),
                    "significant": corr.get("significant", False),
                    "confidence": corr.get("confidence", round((1 - test["p_value"]) * 100, 1)),
                    "uplift": round(test.get("uplift", 0) * 100, 1),
                    "rate": level_aggregates[lv].get("conversion_rate"),
                    "impressions": level_aggregates[lv].get("impressions"),
                    "conversions": level_aggregates[lv].get("conversions"),
                }

            factor_analysis[factor_name] = {
                "control_level": control_level,
                "levels": analysis_levels,
                "aggregates": level_aggregates,
            }

        return factor_analysis

    async def allocate_variant(
        self,
        experiment_id: UUID,
        session_id: str | None = None,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        """Allocate a user to a variant using deterministic hashing.

        Returns the variant config and logs an impression event.
        """
        result = await self.db.execute(
            select(Experiment).where(Experiment.id == experiment_id)
        )
        experiment = result.scalar_one_or_none()

        if not experiment or experiment.status != "running":
            return {"error": "Experiment not found or not running"}

        variants = experiment.variants
        if not variants:
            return {"error": "No variants configured"}

        # Use deterministic hashing for consistent allocation
        if user_id:
            hash_input = f"{experiment_id}:{user_id}"
        elif session_id:
            hash_input = f"{experiment_id}:{session_id}"
        else:
            # Random allocation for anonymous users
            hash_input = f"{experiment_id}:{random.random()}"

        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)

        # Weighted random selection based on traffic_pct
        total_weight = sum(v.get("traffic_pct", 100 // len(variants)) for v in variants)
        position = hash_value % total_weight

        cumulative = 0
        selected_variant = variants[0]
        for variant in variants:
            weight = variant.get("traffic_pct", 100 // len(variants))
            cumulative += weight
            if position < cumulative:
                selected_variant = variant
                break

        # Log impression
        event = ExperimentEvent(
            experiment_id=experiment_id,
            variant_id=selected_variant["id"],
            event_type="impression",
            session_id=session_id,
            user_id=user_id,
        )
        self.db.add(event)
        await self.db.commit()

        return {
            "variant_id": selected_variant["id"],
            "variant_name": selected_variant.get("name", selected_variant["id"]),
            "config": selected_variant.get("config", {}),
        }

    async def track_event(
        self,
        experiment_id: UUID,
        variant_id: str,
        event_type: str,  # conversion, click, revenue
        value: float | None = None,
        session_id: str | None = None,
        user_id: str | None = None,
        source: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Track an event for a variant in an experiment."""
        event = ExperimentEvent(
            experiment_id=experiment_id,
            variant_id=variant_id,
            event_type=event_type,
            value=value,
            session_id=session_id,
            user_id=user_id,
            source=source,
            metadata_=metadata or {},
        )
        self.db.add(event)
        await self.db.commit()

        log.info("experiment_event_tracked",
                experiment=str(experiment_id),
                variant=variant_id,
                event_type=event_type)

        return {"ok": True}

    async def get_experiment_results(
        self,
        experiment_id: UUID,
    ) -> dict[str, Any]:
        """Compute results for an experiment with statistical significance."""
        result = await self.db.execute(
            select(Experiment).where(Experiment.id == experiment_id)
        )
        experiment = result.scalar_one_or_none()

        if not experiment:
            return {"error": "Experiment not found"}

        variants = experiment.variants
        if not variants:
            return {"error": "No variants"}

        variant_ids = [v["id"] for v in variants]
        control_id = experiment.control_variant_id or variant_ids[0]

        # Count events per variant
        results = {}
        for variant_id in variant_ids:
            # Impressions
            impressions_result = await self.db.execute(
                select(func.count())
                .select_from(ExperimentEvent)
                .where(
                    ExperimentEvent.experiment_id == experiment_id,
                    ExperimentEvent.variant_id == variant_id,
                    ExperimentEvent.event_type == "impression",
                )
            )
            impressions = impressions_result.scalar() or 0

            # Conversions
            conversions_result = await self.db.execute(
                select(func.count())
                .select_from(ExperimentEvent)
                .where(
                    ExperimentEvent.experiment_id == experiment_id,
                    ExperimentEvent.variant_id == variant_id,
                    ExperimentEvent.event_type == "conversion",
                )
            )
            conversions = conversions_result.scalar() or 0

            # Clicks
            clicks_result = await self.db.execute(
                select(func.count())
                .select_from(ExperimentEvent)
                .where(
                    ExperimentEvent.experiment_id == experiment_id,
                    ExperimentEvent.variant_id == variant_id,
                    ExperimentEvent.event_type == "click",
                )
            )
            clicks = clicks_result.scalar() or 0

            # Revenue
            revenue_result = await self.db.execute(
                select(func.sum(ExperimentEvent.value))
                .select_from(ExperimentEvent)
                .where(
                    ExperimentEvent.experiment_id == experiment_id,
                    ExperimentEvent.variant_id == variant_id,
                    ExperimentEvent.event_type == "revenue",
                )
            )
            revenue = revenue_result.scalar() or 0.0

            # Revenue per impression
            revenue_count_result = await self.db.execute(
                select(func.count())
                .select_from(ExperimentEvent)
                .where(
                    ExperimentEvent.experiment_id == experiment_id,
                    ExperimentEvent.variant_id == variant_id,
                    ExperimentEvent.event_type == "revenue",
                )
            )
            revenue_count = revenue_count_result.scalar() or 0

            conversion_rate = conversions / impressions if impressions > 0 else 0
            ctr = clicks / impressions if impressions > 0 else 0
            revenue_per_session = revenue / impressions if impressions > 0 else 0

            results[variant_id] = {
                "variant_id": variant_id,
                "variant_name": next((v.get("name", v["id"]) for v in variants if v["id"] == variant_id), variant_id),
                "impressions": impressions,
                "conversions": conversions,
                "clicks": clicks,
                "revenue": revenue,
                "revenue_count": revenue_count,
                "conversion_rate": round(conversion_rate * 100, 2),
                "ctr": round(ctr * 100, 2),
                "revenue_per_session": round(revenue_per_session, 2),
            }

        # Statistical tests (with Bonferroni correction for MVT)
        control = results.get(control_id)
        statistical_tests = {}
        num_variants = len([v for v in variant_ids if v != control_id])

        if control and control["impressions"] >= experiment.min_sample_size and num_variants > 0:
            # Build raw p-values for each metric
            conv_p_values: dict[str, float] = {}
            ctr_p_values: dict[str, float] = {}
            conv_tests: dict[str, Any] = {}
            ctr_tests: dict[str, Any] = {}

            for variant_id, variant_data in results.items():
                if variant_id == control_id:
                    continue
                if variant_data["impressions"] < experiment.min_sample_size:
                    continue

                conv_test = two_proportion_z_test(
                    control["conversions"],
                    control["impressions"],
                    variant_data["conversions"],
                    variant_data["impressions"],
                )
                conv_p_values[variant_id] = conv_test["p_value"]
                conv_tests[variant_id] = conv_test

                ctr_test = two_proportion_z_test(
                    control["clicks"],
                    control["impressions"],
                    variant_data["clicks"],
                    variant_data["impressions"],
                )
                ctr_p_values[variant_id] = ctr_test["p_value"]
                ctr_tests[variant_id] = ctr_test

            # Bonferroni correction for MVT
            use_correction = experiment.experiment_type == "mvt"
            conv_corrected = bonferroni_correction(conv_p_values) if use_correction else {
                k: {"significant": v < 0.05, "p_value": round(v, 4), "corrected_alpha": 0.05,
                    "confidence": round((1 - v) * 100, 1)}
                for k, v in conv_p_values.items()
            }
            ctr_corrected = bonferroni_correction(ctr_p_values) if use_correction else {
                k: {"significant": v < 0.05, "p_value": round(v, 4), "corrected_alpha": 0.05,
                    "confidence": round((1 - v) * 100, 1)}
                for k, v in ctr_p_values.items()
            }

            for variant_id in conv_tests:
                control_rate = control["conversions"] / max(control["impressions"], 1)
                v_rate = results[variant_id]["conversions"] / max(results[variant_id]["impressions"], 1)
                conv_corr = conv_corrected.get(variant_id, {})
                ctr_corr = ctr_corrected.get(variant_id, {})
                conv_test = conv_tests[variant_id]
                ctr_test = ctr_tests[variant_id]

                statistical_tests[variant_id] = {
                    "conversion_rate": {
                        "p_value": round(conv_test["p_value"], 4),
                        "corrected_alpha": conv_corr.get("corrected_alpha", 0.05),
                        "significant": conv_corr.get("significant", False),
                        "confidence": conv_corr.get("confidence", round((1 - conv_test["p_value"]) * 100, 1)),
                        "uplift": round((v_rate - control_rate) / control_rate * 100, 1) if control_rate > 0 else 0.0,
                        "bonferroni_applied": use_correction,
                    },
                    "ctr": {
                        "p_value": round(ctr_test["p_value"], 4),
                        "corrected_alpha": ctr_corr.get("corrected_alpha", 0.05),
                        "significant": ctr_corr.get("significant", False),
                        "confidence": ctr_corr.get("confidence", round((1 - ctr_test["p_value"]) * 100, 1)),
                        "uplift": round((ctr_test.get("uplift", 0)) * 100, 1),
                        "bonferroni_applied": use_correction,
                    },
                }

        # Determine winner
        winner = None
        confidence = None
        uplift = None

        primary_metric = experiment.primary_metric
        if statistical_tests:
            for variant_id, tests in statistical_tests.items():
                metric_test = tests.get("conversion_rate" if primary_metric == "conversion_rate" else "ctr")
                if metric_test and metric_test["significant"]:
                    if winner is None or (metric_test.get("uplift", 0) or 0) > (uplift or 0):
                        winner = variant_id
                        confidence = metric_test["confidence"]
                        uplift = metric_test.get("uplift", 0)

        # Auto-stop check
        if experiment.auto_stop and winner and experiment.status == "running":
            experiment.status = "completed"
            experiment.winner = winner
            experiment.confidence = confidence
            experiment.uplift = uplift / 100 if uplift else None
            experiment.ended_at = datetime.utcnow()
            await self.db.commit()

            log.info("experiment_auto_stopped",
                    experiment=str(experiment_id),
                    winner=winner,
                    confidence=confidence)

        # Factor analysis for MVT experiments
        factor_analysis = {}
        factors = experiment.factors or {}
        if experiment.experiment_type == "mvt" and factors and results:
            # Attach factor_levels to results
            for variant in experiment.variants:
                fl = variant.get("factor_levels", {})
                vid = variant["id"]
                if vid in results:
                    results[vid]["factor_levels"] = fl

            factor_analysis = self.compute_factor_analysis(results, factors, control_id)

        return {
            "experiment_id": str(experiment_id),
            "experiment_name": experiment.name,
            "experiment_type": experiment.experiment_type,
            "hypothesis": experiment.hypothesis,
            "status": experiment.status,
            "primary_metric": primary_metric,
            "control_variant": control_id,
            "results": results,
            "statistical_tests": statistical_tests,
            "factor_analysis": factor_analysis,
            "factors": factors,
            "winner": winner,
            "confidence": confidence,
            "uplift": uplift,
            "min_sample_size": experiment.min_sample_size,
            "min_confidence": experiment.min_confidence,
        }

    async def start_experiment(self, experiment_id: UUID) -> dict[str, Any]:
        """Start an experiment."""
        result = await self.db.execute(
            select(Experiment).where(Experiment.id == experiment_id)
        )
        experiment = result.scalar_one_or_none()

        if not experiment:
            return {"error": "Experiment not found"}
        if experiment.status == "running":
            return {"error": "Already running"}

        experiment.status = "running"
        experiment.started_at = datetime.utcnow()
        await self.db.commit()

        return {"id": str(experiment_id), "status": "running"}

    async def stop_experiment(self, experiment_id: UUID) -> dict[str, Any]:
        """Stop an experiment and compute final results."""
        result = await self.db.execute(
            select(Experiment).where(Experiment.id == experiment_id)
        )
        experiment = result.scalar_one_or_none()

        if not experiment:
            return {"error": "Experiment not found"}

        experiment.status = "stopped"
        experiment.ended_at = datetime.utcnow()
        await self.db.commit()

        # Compute final results
        return await self.get_experiment_results(experiment_id)
