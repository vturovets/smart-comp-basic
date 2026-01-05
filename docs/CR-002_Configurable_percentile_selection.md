# CR-002: Configurable Percentile Selection (P90/P95)

**Owner:** vturovets  
**Repo:** `vturovets/smart-comp`

**Tags:** statistics, performance, percentile, bootstrap, CLI

---

## 1) Summary

Smart‑Comp currently hard-codes the 95th percentile (P95) as the tail metric for  
hypothesis testing and descriptive summaries. This change request proposes to  
make the percentile configurable so that users can choose between P90 and P95  
(or other values in the future). When enabled, the tool will read a  
`percentile` setting from the configuration (default: 95) and will compute  
bootstrap estimates, confidence intervals, p‑values and margins of error for the  
selected percentile. All result keys and output labels will reflect the chosen  
percentile (e.g. `p90_1`, `p90_2`, `ci lower p90_1`). The legacy P95  
behaviour will be preserved as the default to maintain backward compatibility.

---

## 2) Business Rationale

Different teams may prefer to monitor the 90th percentile (P90) of latency  
instead of the 95th percentile (P95). P90 is less sensitive to extreme  
outliers and provides a broader view of typical tail performance, which can be  
useful for services with highly volatile top 5 % response times. Supporting  
both P90 and P95 allows Smart‑Comp to adapt to diverse service level objectives  
(SLOs) and aligns the tool with industry‑standard APM dashboards that often  
report multiple percentiles.

---

## 3) Scope

**In scope**

- Read a new integer `percentile` option from the `[test]` section of  
  `config.txt` (default: `95`).

- Update bootstrapping helpers to accept an arbitrary percentile and return  
  result dictionaries with dynamically named keys (e.g. `p{percentile}_1`).

- Preserve existing functions (`compare_p95s`, `compare_p95_to_threshold`) for  
  backward compatibility by wrapping the new generic helpers.

- Modify the CLI flow to:
  
  - Use the configured percentile when sampling and testing.
  
  - Name result entries based on the percentile  
    (e.g. `003_comp_2_P90s` instead of `003_comp_2_P95s`).
  
  - Update help strings to describe “Compare PXX values” rather than always  
    referring to P95.

- Extend the `[output]` section of `config.txt` with toggles for the new keys:  
  `p90_1`, `p90_2`, `ci lower p90_1`, `ci upper p90_1`, `p90_1_moe`,  
  `p90_2_moe`, and `p90_1_empirical`, `p90_2_empirical`.

- Update the interpretation engine to detect which percentile was analysed and  
  adjust the narrative accordingly (e.g. “95th percentile (P95)” → “90th  
  percentile (P90)”).

- Update documentation (`README.md`) and examples to reflect the new option.

- Add a new pytest case to ensure that selecting `percentile = 90` in the  
  configuration produces result keys labelled `p90_*` and that the default  
  remains `p95_*`.

**Out of scope**

- Allowing multiple percentiles to be computed in a single run (future CR).

- Changing the default percentile of the Kruskal–Wallis permutation command,  
  which will continue to report P95 in the summary CSV.

---

## 4) Data Contract (input)

No changes to the input format. The tool will continue to accept one or two  
CSV files containing a single numeric `value` column. The percentile chosen  
only affects which quantile of the cleaned and sampled data is used for  
statistical comparisons. Users should ensure that any threshold specified in  
`config.txt` corresponds to the same percentile (e.g. a P90 threshold should be  
lower than a P95 threshold for the same SLO).

## 5) CLI Design

- Add a new configuration parameter under `[test]`:
  
  ```ini
  # Percentile to analyse (e.g. 90 or 95). Default = 95.
  percentile = 95
  ```

- Optionally allow overriding the percentile via an environment variable or  
  future CLI flag. For this change request, configuration only is sufficient.

- The legacy CLI invocation remains unchanged:
  
  ```
  python cli.py <input_1.csv> [input_2.csv] [output.txt]
  ```

- The CLI help message should be updated to read:
  
  > Hypothesis Testing Tool: Compare selected percentile values (default P95)  
  > from one or two datasets.

- Result section keys in the console and any output files should reflect the  
  chosen percentile. For example, if `percentile = 90` then the key for the  
  two‑sample test becomes `003_comp_2_P90s` and the printed fields start with  
  `p90_1`, `p90_2`, etc.

## 6) Method (High Level)

1. **Bootstrap helper generalisation**: Introduce two new internal functions,  
   `compare_percentiles(p_sample1, p_sample2, percentile, sample_size, alpha)`  
   and `compare_percentile_to_threshold(p_samples, threshold, percentile, sample_size, alpha)`. These functions implement the current logic of  
   `compare_p95s` and `compare_p95_to_threshold` but construct their result  
   dictionaries using dynamic key names such as `p90_1`. The existing P95  
   functions become thin wrappers that call the new generic helpers with  
   `percentile=95`.

2. **Configuration reading**: In `run_bootstrap_test` and  
   `run_bootstrap_single_sample_test`, read the integer `percentile` from the  
   configuration with a fallback to `95`. Pass this value to  
   `bootstrap_percentile` and the new comparison helpers.

3. **Result labelling**: When merging top‑level fields, construct the  
   operation string and the result dictionary names using the selected  
   percentile. For example, `operation = "comparing two P90s"` and  
   `results["003_comp_2_P90s"] = …`.

4. **Empirical percentiles**: When the output configuration enables  
   `p{percentile}_1_empirical` or `p{percentile}_2_empirical`, compute the  
   empirical percentile using `np.percentile(data["value"], percentile)` and  
   assign it to the corresponding dynamic key.

5. **Interpretation updates**: Modify `interpretation/engine.py` to:
   
   - Inject the chosen percentile into the prompt when calling the OpenAI API.
   
   - In the fallback `simple_local_interpretation` function, detect the  
     percentile by inspecting the keys of the result dictionary (e.g. find the  
     substring between `p` and `_1`) and use it to look up the mean estimates,  
     margins of error and empirical values. Update narrative strings to  
     mention “P90” or “P95” accordingly.

6. **Documentation and tests**: Document the new `percentile` option in the  
   README and add a new test case that sets `percentile = 90` in a temporary  
   configuration and asserts that the result keys and summaries use `p90_*`  
   names. Ensure that existing tests (which rely on the default P95) continue  
   to pass.

## 7) Acceptance Criteria

- ✅ When `percentile = 90` is specified in the configuration, the bootstrapping  
  helpers compute the P90, and the result dictionaries use keys prefixed with  
  `p90_`.

- ✅ The CLI displays and writes outputs using names like `003_comp_2_P90s`  
  instead of `003_comp_2_P95s` when the percentile is set to 90.

- ✅ When the percentile is omitted or set to 95, the tool behaves exactly as  
  before (backward compatibility).

- ✅ The interpretation engine correctly mentions the selected percentile in  
  both the OpenAI‑powered and local fallbacks.

- ✅ The default configuration file includes toggles for both P95 and P90  
  output fields, with P95 enabled by default and P90 disabled.

- ✅ Unit tests covering both percentiles are added, and all existing tests  
  continue to pass.

## 8) Error Handling

- If the `percentile` value in the configuration is not an integer between 1  
  and 99, the tool should raise a clear error (e.g. “Invalid percentile: must be  
  between 1 and 99”).

- If users forget to adjust the `threshold` when switching from P95 to P90, the  
  documentation should warn that thresholds are percentile‑specific.

## 9) Performance Considerations

Computing P90 instead of P95 slightly reduces the variance of bootstrap  
estimates and does not materially change performance. The bootstrap and  
significance logic remain the same.

## 10) Tests (High Level)

- **Default percentile**: run an existing two‑sample test with the default  
  configuration and assert that the keys begin with `p95_` and that the  
  numerical results are unchanged relative to the current version.

- **Alternate percentile**: set `percentile = 90` in a test configuration and  
  run both single‑sample and two‑sample workflows on known data. Assert that  
  keys begin with `p90_` and that the printed operation strings include  
  “P90”.

- **Interpretation**: ensure that the fallback interpretation mentions “90th  
  percentile” when appropriate.

## 11) Documentation

- Update `config.txt` to include `percentile = 95` in the `[test]` section  
  and add toggles for `p90_*` fields in the `[output]` section.

- Modify `README.md` to explain the new `percentile` option, its rationale and  
  example usage for comparing P90 vs P95.

- Provide a short note on selecting appropriate thresholds when switching  
  percentiles.

## 12) Risks & Mitigations

- **Key mismatch in output**: If users enable `p90_*` fields without setting  
  `percentile = 90`, the corresponding values will be `None`. Mitigate by  
  documenting that output toggles should match the selected percentile.

- **Backward compatibility**: Code must ensure that existing integrations  
  relying on the P95 keys continue to work. This is addressed by keeping  
  `compare_p95s` and using P95 as the default.

- **User confusion**: Provide clear guidance in the README on the differences  
  between P90 and P95 and when to choose each.

## 13) Rollout

1. Implement code changes and update the configuration file and docs.

2. Add the new test cases and ensure the full test suite passes.

3. Merge into `main`.

4. Tag a minor release (e.g. v0.2.0) and announce the availability of  
   configurable percentiles.
