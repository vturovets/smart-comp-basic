"""Interpretation helpers for CLI results."""

from __future__ import annotations

import json

import openai

from smart_comp.utils import sanitize_for_json


def interpret_results(results, config):
    try:
        if config.getboolean("interpretation", "use_chatgpt_api", fallback=False):
            client = openai.OpenAI(api_key=config.get("interpretation", "openai_api_key"))

            sanitized_results = sanitize_for_json(results)
            prompt = f"""
You are an expert in statistical analysis for IT system performance evaluation.

Here is the data from a recent hypothesis testing comparing 95th percentiles (P95) using bootstrapping.

[RESULTS]
```json
{json.dumps(sanitized_results, indent=2)}
```

Important Instructions:
- Base your interpretation strictly and exclusively on the provided results.
- Do not perform any additional statistical calculations.
- If information is missing, do not invent or assume anything.
- Summarize the findings exactly as presented.
- Focus only on the fields explicitly given in the data.

Your task:
1. Summarize the statistical findings clearly and concisely.
2. State whether a statistically significant difference was detected, and explain what it means.
3. Analyze the provided confidence intervals and margins of error (MoE) — based only on given data.
4. If a threshold comparison was provided, explain it based on the data.
5. Based on the results, provide clear and practical recommendations.
6. Please avoid stating that the distribution is unimodal if:
- KDE Peak Count > 1
- Dip Test p-value < 0.05
- Bimodality Coefficient > 0.55

Format:
- Output everything in Markdown format.
- Use bold section headers like ## Summary and ## Recommendations.
- Start with a short summary.
- Then list recommendations as bullet points.
- Be cautious: if results are borderline, reflect the uncertainty.
- Style: Executive summary for non-statisticians (business analysts, project managers).
"""

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=800,
            )
            interpretation_text = response.choices[0].message.content.strip()
        else:
            interpretation_text = simple_local_interpretation(results)
    except Exception as exc:
        print(f"[Warning] GPT interpretation failed: {exc}")
        interpretation_text = simple_local_interpretation(results)

    return interpretation_text


def simple_local_interpretation(results):
    try:
        for section in results:
            if isinstance(results[section], dict) and "significant difference" in results[section]:
                r = results[section]
                break
        else:
            return "No valid test results found."

        p_value = r.get("p-value")
        alpha = r.get("alpha", 0.05)
        significant = r.get("significant difference")
        p95_1 = r.get("p95_1_empirical") or r.get("p95_1")
        p95_2 = r.get("p95_2_empirical") or r.get("p95_2")
        threshold = r.get("threshold")
        moe_1 = r.get("p95_1_moe")
        moe_2 = r.get("p95_2_moe")

        text = []
        text.append("## Summary of Statistical Findings:")

        if p_value is not None:
            text.append(f"- **P-value** = {p_value:.3f} (alpha = {alpha:.2f})")

        if significant is not None:
            if significant:
                text.append("- **Result**: A statistically significant difference was detected.")
            else:
                text.append("- **Result**: No statistically significant difference was detected.")

        if threshold is not None and p95_1 is not None:
            if p95_1 <= threshold:
                text.append(f"- The P95 ({p95_1:.1f}) is within the threshold ({threshold}). ✅")
            else:
                text.append(f"- The P95 ({p95_1:.1f}) exceeds the threshold ({threshold}). ⚠️")

        if p95_1 is not None and p95_2 is not None:
            text.append(f"- P95 of Sample 1: {p95_1:.1f}")
            text.append(f"- P95 of Sample 2: {p95_2:.1f}")

        if moe_1 is not None:
            text.append(f"- Margin of Error for Sample 1: ±{moe_1:.1f}%")
        if moe_2 is not None:
            text.append(f"- Margin of Error for Sample 2: ±{moe_2:.1f}%")

        text.append("\n## Recommendations:")

        if significant and (p_value is not None and p_value < alpha):
            text.append("- Proceed with decision-making based on the observed difference.")
        elif p_value is not None and abs(p_value - alpha) < 0.02:
            text.append("- Results are borderline significant; consider collecting more data.")
        else:
            text.append("- No strong evidence of difference; monitor further if needed.")

        if (moe_1 and moe_1 > 10) or (moe_2 and moe_2 > 10):
            text.append(
                "- Large margin of error detected. Larger sample size is recommended for more precise estimation."
            )

        return "\n".join(text)
    except Exception as exc:
        return f"[Error in local interpretation: {exc}]"
