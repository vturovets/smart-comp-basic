"""Interpretation helpers for CLI results."""

from __future__ import annotations

import json

import openai

from smart_comp.utils import sanitize_for_json


def _infer_percentile_from_results(results: dict) -> int:
    for section in results.values():
        if isinstance(section, dict):
            for key in section:
                if key.startswith("p") and "_" in key and key[1:key.find("_")].isdigit():
                    return int(key[1 : key.find("_")])
    return 95


def interpret_results(results, config):
    try:
        if config.getboolean("interpretation", "use_chatgpt_api", fallback=False):
            client = openai.OpenAI(api_key=config.get("interpretation", "openai_api_key"))

            sanitized_results = sanitize_for_json(results)
            percentile = _infer_percentile_from_results(results)
            prompt = f"""
You are an expert in statistical analysis for IT system performance evaluation.

Here is the data from a recent hypothesis testing comparing {percentile}th percentiles (P{percentile}) using bootstrapping.

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

        percentile = _infer_percentile_from_results(results)
        perc_label = f"P{percentile}"
        p_key_1 = f"p{percentile}_1"
        p_key_2 = f"p{percentile}_2"
        moe_key_1 = f"p{percentile}_1_moe"
        moe_key_2 = f"p{percentile}_2_moe"
        empirical_key_1 = f"p{percentile}_1_empirical"
        empirical_key_2 = f"p{percentile}_2_empirical"

        p_value = r.get("p-value")
        alpha = r.get("alpha", 0.05)
        significant = r.get("significant difference")
        p95_1 = r.get(empirical_key_1) or r.get(p_key_1)
        p95_2 = r.get(empirical_key_2) or r.get(p_key_2)
        threshold = r.get("threshold")
        moe_1 = r.get(moe_key_1)
        moe_2 = r.get(moe_key_2)

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
                text.append(f"- The {perc_label} ({p95_1:.1f}) is within the threshold ({threshold}). ✅")
            else:
                text.append(f"- The {perc_label} ({p95_1:.1f}) exceeds the threshold ({threshold}). ⚠️")

        if p95_1 is not None and p95_2 is not None:
            text.append(f"- {perc_label} of Sample 1: {p95_1:.1f}")
            text.append(f"- {perc_label} of Sample 2: {p95_2:.1f}")

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
