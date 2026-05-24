"""Auto-Prompt Optimization Engine — AI-powered prompt engineering.

Automatically optimizes prompts by:
- A/B testing prompt variants
- Measuring output quality metrics
- Applying best practices (few-shot, chain-of-thought, etc.)
- Learning from successful completions
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any

from helix.core.config import get_settings
from helix.core.logging import get_logger
from helix.llm.gateway import complete

log = get_logger("helix.prompt_optimizer")
settings = get_settings()


@dataclass
class PromptVariant:
    """A prompt variant for testing."""
    id: str
    template: str
    system_prompt: str | None = None
    few_shot_examples: list[dict[str, str]] | None = None
    temperature: float = 0.7
    metadata: dict[str, Any] | None = None


@dataclass
class PromptTest:
    """A test case for prompt optimization."""
    input_data: str
    expected_output: str | None = None
    evaluation_criteria: list[str] | None = None


class PromptOptimizer:
    """Optimize prompts through systematic testing."""

    def __init__(self) -> None:
        self._history: list[dict[str, Any]] = []

    async def generate_variants(
        self,
        base_prompt: str,
        num_variants: int = 3,
    ) -> list[PromptVariant]:
        """Generate prompt variants using an LLM."""
        system = """You are an expert prompt engineer. Given a base prompt, generate improved variants.

Create variants that:
1. Add clarity and specificity
2. Include examples (few-shot)
3. Use chain-of-thought reasoning
4. Add output format specifications
5. Include edge case handling

Return a JSON array of prompt variants. Each variant should be meaningfully different."""

        prompt = f"Base prompt:\n{base_prompt}\n\nGenerate {num_variants} improved variants."

        try:
            result = await complete(
                model="openai:gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                system=system,
                temperature=0.8,
                json_mode=True,
            )
            variants_data = json.loads(result.text)

            variants = []
            for i, v in enumerate(variants_data.get("variants", variants_data if isinstance(variants_data, list) else [])):
                variants.append(PromptVariant(
                    id=f"v{i+1}",
                    template=v.get("prompt", v.get("template", base_prompt)),
                    system_prompt=v.get("system_prompt"),
                    few_shot_examples=v.get("few_shot_examples"),
                    temperature=v.get("temperature", 0.7),
                ))
            return variants
        except Exception:
            log.exception("variant_generation_failed")
            return [PromptVariant(id="v1", template=base_prompt)]

    async def evaluate_prompt(
        self,
        variant: PromptVariant,
        test_cases: list[PromptTest],
    ) -> dict[str, Any]:
        """Evaluate a prompt variant against test cases."""
        scores = []
        latencies = []
        tokens = []

        for test in test_cases:
            start = time.time()
            try:
                messages = []
                if variant.few_shot_examples:
                    for ex in variant.few_shot_examples:
                        messages.append({"role": "user", "content": ex["input"]})
                        messages.append({"role": "assistant", "content": ex["output"]})

                messages.append({"role": "user", "content": test.input_data})

                result = await complete(
                    model="openai:gpt-4o",
                    messages=messages,
                    system=variant.system_prompt or "You are a helpful assistant.",
                    temperature=variant.temperature,
                )

                latency = time.time() - start
                latencies.append(latency)
                tokens.append(result.prompt_tokens or 0 + result.completion_tokens or 0)

                # Score output quality
                score = await self._score_output(
                    result.text,
                    test.expected_output,
                    test.evaluation_criteria,
                )
                scores.append(score)

            except Exception as exc:
                scores.append(0.0)
                log.warning("prompt_test_failed", error=str(exc))

        avg_score = sum(scores) / len(scores) if scores else 0
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        avg_tokens = sum(tokens) / len(tokens) if tokens else 0

        return {
            "variant_id": variant.id,
            "avg_score": round(avg_score, 3),
            "avg_latency_ms": round(avg_latency * 1000, 2),
            "avg_tokens": round(avg_tokens, 1),
            "test_count": len(test_cases),
            "scores": scores,
        }

    async def _score_output(
        self,
        actual: str,
        expected: str | None,
        criteria: list[str] | None,
    ) -> float:
        """Score output quality."""
        if not expected and not criteria:
            return 1.0

        scores = []

        # Exact match score
        if expected:
            if actual.strip().lower() == expected.strip().lower():
                scores.append(1.0)
            else:
                # Semantic similarity using simple heuristic
                common = len(set(actual.lower().split()) & set(expected.lower().split()))
                total = len(set(actual.lower().split()) | set(expected.lower().split()))
                scores.append(common / total if total > 0 else 0)

        # Criteria check
        if criteria:
            for criterion in criteria:
                # Check if criterion keywords appear in output
                keywords = criterion.lower().split()
                matches = sum(1 for k in keywords if k in actual.lower())
                scores.append(matches / len(keywords) if keywords else 1.0)

        return sum(scores) / len(scores) if scores else 0.5

    async def optimize(
        self,
        base_prompt: str,
        test_cases: list[PromptTest],
        num_variants: int = 3,
    ) -> dict[str, Any]:
        """Run full optimization pipeline."""
        log.info("prompt_optimization_start", test_cases=len(test_cases))

        # Generate variants
        variants = await self.generate_variants(base_prompt, num_variants)
        log.info("variants_generated", count=len(variants))

        # Evaluate each variant
        results = []
        for variant in variants:
            result = await self.evaluate_prompt(variant, test_cases)
            results.append({
                "variant": variant,
                **result,
            })

        # Rank by score (primary) and latency (secondary)
        results.sort(key=lambda r: (-r["avg_score"], r["avg_latency_ms"]))

        best = results[0]
        improvement = best["avg_score"] - (results[-1]["avg_score"] if len(results) > 1 else 0)

        log.info(
            "prompt_optimization_complete",
            best_variant=best["variant_id"],
            score=best["avg_score"],
            improvement=round(improvement, 3),
        )

        return {
            "base_prompt": base_prompt,
            "best_variant": {
                "id": best["variant_id"],
                "template": best["variant"].template,
                "system_prompt": best["variant"].system_prompt,
                "temperature": best["variant"].temperature,
            },
            "score": best["avg_score"],
            "latency_ms": best["avg_latency_ms"],
            "all_results": [
                {
                    "id": r["variant_id"],
                    "score": r["avg_score"],
                    "latency_ms": r["avg_latency_ms"],
                    "template": r["variant"].template[:200] + "...",
                }
                for r in results
            ],
            "improvement": round(improvement, 3),
        }

    async def auto_improve(
        self,
        prompt: str,
        recent_completions: list[dict[str, Any]],
    ) -> str:
        """Auto-improve a prompt based on recent completion patterns."""
        if not recent_completions:
            return prompt

        # Analyze patterns in recent completions
        good_examples = [c for c in recent_completions if c.get("score", 0) > 0.7]
        bad_examples = [c for c in recent_completions if c.get("score", 0) < 0.4]

        if not good_examples and not bad_examples:
            return prompt

        analysis_prompt = f"""Original prompt:\n{prompt}\n\n"

Good completions ({len(good_examples)}):
{json.dumps([{"input": c["input"], "output": c["output"][:200]} for c in good_examples[:3]], indent=2)}

Bad completions ({len(bad_examples)}):
{json.dumps([{"input": c["input"], "output": c["output"][:200], "error": c.get("error", "")} for c in bad_examples[:3]], indent=2)}

Improve the prompt to:
1. Emphasize patterns that led to good results
2. Add clarifications to avoid bad result patterns
3. Keep it concise and focused

Return ONLY the improved prompt, no explanation."""

        try:
            result = await complete(
                model="openai:gpt-4o",
                messages=[{"role": "user", "content": analysis_prompt}],
                temperature=0.5,
            )
            improved = result.text.strip()
            if improved and len(improved) > 20:
                log.info("prompt_auto_improved", original_len=len(prompt), improved_len=len(improved))
                return improved
        except Exception as exc:
            log.warning("auto_improve_failed", error=str(exc))

        return prompt


# Global instance
_optimizer: PromptOptimizer | None = None


def get_prompt_optimizer() -> PromptOptimizer:
    global _optimizer
    if _optimizer is None:
        _optimizer = PromptOptimizer()
    return _optimizer
