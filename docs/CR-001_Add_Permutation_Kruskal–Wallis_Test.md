# CR-001: Add Permutation Kruskal–Wallis Test (multi-sample, raw durations from folder)

**Owner:** Volodymyr  
**Repo:** `vturovets/smart-comp`  

**Tags:** statistics, nonparametric, performance, hypothesis-testing, CLI

---

## 1) Summary

Add a command to compare **N ≥ 2 latency samples** (CSV files of raw durations) using a **Permutation Kruskal–Wallis** omnibus test. The tool will:

- Read all `.csv` files from a target folder (each file = 1 group).

- Compute the **Kruskal–Wallis H** statistic on actual labels.

- Generate a **permutation p-value** by shuffling labels **while preserving group sizes**.

- Output H, permutation p, group counts, and basic tail metrics (median/P95 per file) for context.

- (Optional flag) Write a small report to CSV/JSON.

---

## 2) Business Rationale

- We frequently observe **non-normal, heavy-tailed** response times.

- Need an **assumption-light omnibus** test to check if multiple windows/samples differ materially.

- Supports decisions like: “Set a single P95 requirement vs. segment by peak/off-peak.”

---

## 3) Scope

**In scope**

- New Python module implementing Kruskal–Wallis statistic + label-permutation.

- Folder-based ingestion of multiple CSVs (each contains raw duration values).

- CLI command with parameters (`--folder`, `--pattern`, `--permutations`, `--seed`, `--format`).

- Summary table (per group: n, median, P95) and final test result (H, p).

**Out of scope**

- Pairwise post-hoc tests (could be a follow-up CR).

- Multiple metrics per row (assume a single duration column).

- Very large file streaming optimizations beyond basic memory-safe reading.

---

## 4) Data Contract (input)

- **Folder** containing files matching a pattern (default: `*.csv`).

- **Each CSV**: one column of numeric durations in milliseconds (header optional).
  
  - Autodetect first numeric column if headers are unknown; or specify `--column name`.

- **Groups**: 1 file = 1 group.

---

## 5) CLI Design

**New command:** `smart-comp kw-permutation`

**Args (proposed):**

- `--folder PATH` (required): folder with CSVs.

- `--pattern STR` (optional, default `*.csv`): glob pattern.

- `--column STR|INT` (optional): column name or 0-based index.

- `--permutations INT` (default `10000`): number of permutations.

- `--seed INT` (optional): RNG seed for reproducibility.

- `--report PATH` (optional): write JSON report.

- `--summary-csv PATH` (optional): write per-group summary CSV.

- `--quiet` (optional): minimal console output.

**Example usage:**

```
smart-comp kw-permutation --folder data/windows --pattern "*.csv" --column duration_ms --permutations 10000 --seed 42 --report reports/kw_2025-10-30.json --summary-csv reports/kw_2025-10-30_groups.csv
```

---

## 6) Method (high level)

1. **Load groups:** gather all CSVs; parse target column to NumPy arrays; drop NaNs/negatives.

2. **Compute observed H:** standard Kruskal–Wallis (rank all pooled observations; apply H formula).

3. **Permutation p-value:**
   
   - Pool all observations; record group sizes.
   
   - For each permutation, shuffle pooled values, split back to original group sizes, recompute H.
   
   - `p = (# permutations with H_perm ≥ H_obs) / B`.

4. **Summaries:** for each group, compute `n`, `median`, `P95`.

5. **Output:** print table + H, p; optionally write JSON/CSV.

**Notes**

- This is **distribution-free**; no normality assumption.

- Use **Monte Carlo standard error** to guide `--permutations` choice if needed.

---

## 7) Acceptance Criteria

- ✅ Given ≥2 CSV files in a folder, command runs and prints:
  
  - Per-group summary: file name, `n`, median, P95.
  
  - Omnibus result: `H_obs`, `p_perm`, `permutations`, `total_n`.

- ✅ Results are **stable** with the same `--seed`.

- ✅ Handles mixed group sizes (10k–100k+) without error.

- ✅ Treats non-numeric/blank rows gracefully (ignored; warn count).

- ✅ Optional outputs (`--report`, `--summary-csv`) are created and valid.

---

## 8) Error Handling

- Missing folder / no files match pattern → clear error message.

- Column not found / all non-numeric → clear error.

- Too few groups (<2) → clear error.

- Memory errors → suggest reducing number of files or down-sampling.

---

## 9) Performance Considerations

- Use vectorized NumPy ranking for H.

- Avoid repeated allocations inside permutation loop; pre-allocate buffers.

- For very large pooled N, allow an **optional down-sample** flag (future CR) with clear disclaimer.

---



## 10) Tests (high level)

- **Unit:** deterministic output with fixed seed on synthetic data.
  
  - Case A: all groups sampled from same distribution → expect high p (non-sig).
  
  - Case B: one group shifted/slower → expect low p (sig).

- **I/O:** folder with mixed CSVs; missing column; bad values ignored.

- **Large N:** smoke test with bigger arrays to ensure no crashes/timeouts.

---

## 11) Documentation

- Update `README.md`:
  
  - Purpose, assumptions, and example usage.
  
  - Interpretation of `H` and permutation `p`.
  
  - Tip: report effect sizes (e.g., P95 range) alongside p.

- Add a mini **“Stats Background”** section linking Kruskal–Wallis and permutation rationale.

---

## 12) Risks & Mitigations

- **Runtime for very large N**: allow users to lower `--permutations` or down-sample in future CR.

- **CSV heterogeneity**: add clear error messages and column autodetect.

- **Interpretation misuse**: doc emphasizes that omnibus significance ⇒ “at least one group differs,” not which ones.

---

## 13) Rollout

1. Implement + tests.

2. Run against a known dataset (sanity check with fixed seed).

3. Merge to `main`.

4. Tag minor release and update docs.

---

## 14) Example Output (console)

```
Groups: 18, N=1,240,000, perms=10000
- 2025-10-24.csv: n=85000, median=612.4, p95=884.7
...
H=23.183947, p_perm=0.0312
```

---


