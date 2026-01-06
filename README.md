# Smart-Comp

Smart-Comp is a command-line toolkit for statistically comparing the 95th percentile (P95) of one or two latency or performance datasets.  It automates data cleaning, bootstrapped hypothesis testing, and narrative interpretation so you can determine whether a regression or improvement is statistically significant (see [smart_comp/cli/app.py](smart_comp/cli/app.py)).

## Features

- **Single or dual dataset comparisons** – compare a dataset against a fixed threshold or evaluate the difference between two CSV inputs using bootstrap resampling ([smart_comp/cli/app.py](smart_comp/cli/app.py#L32-L116)).
- **Descriptive statistics pipeline** – optional descriptive summaries (mean, min/max, standard deviation, etc.) generated from cleaned inputs ([smart_comp/cli/app.py](smart_comp/cli/app.py#L59-L79), [smart_comp/io/output.py](smart_comp/io/output.py#L24-L39)).
- **Automated data hygiene** – validates ratio-scale requirements, enforces guardrails, removes outliers, and writes sanitized copies of the inputs ([smart_comp/io/input.py](smart_comp/io/input.py#L10-L35), [smart_comp/validation/checks.py](smart_comp/validation/checks.py#L1-L69)).
- **Autosized sampling** – derives sample sizes tailored to your data before running hypothesis tests ([smart_comp/cli/app.py](smart_comp/cli/app.py#L82-L95), [smart_comp/sampling/autosize.py](smart_comp/sampling/autosize.py#L1-L34)).
- **Result interpretation** – optional Markdown explanations and visualization call-outs help communicate findings to stakeholders ([smart_comp/cli/app.py](smart_comp/cli/app.py#L117-L153)).
- **Configurable outputs** – toggle log creation, text exports, histograms, KDE plots, and more from a simple INI configuration file ([config.txt](config.txt#L1-L58)).

## Project layout

```
.
├── cli.py                  # Entry point wrapper around the CLI application
├── config.txt              # Default configuration consumed by the CLI
├── smart_comp/             # Library code (analysis, IO, sampling, stats, etc.)
└── tests/                  # Pytest suite covering core behaviours
```

Sample CSV inputs (single-column, headerless) are included at the repository root for experimentation.

## Requirements

Runtime dependencies – NumPy, pandas, SciPy, Matplotlib, diptest, and optional OpenAI APIs – are listed in `requirements.txt` alongside version pins ([requirements.txt](requirements.txt#L1-L6)). For development work the test suite uses `pytest` ([requirements-dev.txt](requirements-dev.txt#L1-L2)).

## Installation

1. Create and activate a virtual environment.
2. Install runtime dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. (Optional) Install development extras to run the tests:

   ```bash
   pip install -r requirements-dev.txt
   ```

If you intend to generate AI-assisted interpretations, export `OPENAI_API_KEY` or provide a key in `config.txt` under `[interpretation]`.

## Usage

Run the CLI from the project root. Two entry points are available:

### Legacy bootstrap comparison

```bash
python cli.py <input_1.csv> [input_2.csv] [results.txt]
```

- **Single input:** compares the dataset against the `[test] threshold` configured in `config.txt` and emits hypothesis test statistics for the sample percentile (default P95) ([smart_comp/cli/app.py](smart_comp/cli/app.py#L46-L87)).
- **Two inputs:** compares the selected percentile between the datasets using paired bootstrap resampling ([smart_comp/cli/app.py](smart_comp/cli/app.py#L88-L115)).
- **Output file:** if provided, the formatted results are written to disk; otherwise they are printed to stdout ([smart_comp/io/output.py](smart_comp/io/output.py#L8-L39)).

By default the bootstrap flow will:

1. Clean and validate each CSV, ensuring a single numeric `value` column and applying outlier thresholds ([smart_comp/io/input.py](smart_comp/io/input.py#L10-L35)).
2. Optionally produce descriptive statistics (`[descriptive analysis] required = True`).
3. Run unimodality checks (if enabled) before sampling.
4. Auto-sample cleaned data to the configured size and execute the bootstrap hypothesis test at the configured percentile ([smart_comp/cli/app.py](smart_comp/cli/app.py#L82-L109)).
5. Save the results and (optionally) generate interpretation Markdown with links to any plots the configuration enables ([smart_comp/cli/app.py](smart_comp/cli/app.py#L117-L153)).

### Kruskal–Wallis permutation command

Use the dedicated sub-command to analyse multiple latency groups stored in a folder of CSVs:

```bash
python cli.py kw-permutation \
  --folder path/to/groups \
  --pattern "*.csv" \
  --column duration \
  --permutations 5000 \
  --seed 1234 \
  --report report.json \
  --summary-csv summary.csv
```

- `--folder` and `--pattern` describe where to locate the CSV files. At least two files must be found or the command exits with an error ([smart_comp/io/folder_loader.py](smart_comp/io/folder_loader.py#L31-L74)).
- `--column` can be omitted to auto-detect the first numeric column. Pass a header name or zero-based index to override detection ([smart_comp/io/folder_loader.py](smart_comp/io/folder_loader.py#L76-L120)).
- `--permutations` and `--seed` control the permutation test reproducibility ([smart_comp/stats/kruskal.py](smart_comp/stats/kruskal.py#L32-L83)).
- Optional `--report` and `--summary-csv` arguments persist JSON and CSV outputs alongside the console table ([smart_comp/cli/kw_permutation.py](smart_comp/cli/kw_permutation.py#L16-L73)).

The console report lists per-group medians, P95 values, dropped-row counts, and the omnibus statistics. The JSON payload includes the observed Kruskal–Wallis H statistic, tie-correction factor, permutation distribution metadata, and (if provided) the RNG seed used for shuffling labels ([smart_comp/cli/kw_permutation.py](smart_comp/cli/kw_permutation.py#L75-L157)).

**Interpreting H and permutation p-values:** H measures how different the group rank sums are—the larger the value, the more evidence of distributional shifts between groups. The permutation p-value reports the fraction of shuffled label assignments whose H statistic is at least as extreme as the observed one. Small p-values (e.g., `< 0.05`) indicate the observed H is unlikely under the null hypothesis that all files were drawn from the same distribution, while larger p-values suggest no statistically detectable shift ([smart_comp/stats/kruskal.py](smart_comp/stats/kruskal.py#L32-L111)).

### Configuration

All behaviour is driven by `config.txt`. The tables below list every available option with its description and the default value shipped in this repository (the CLI also applies sensible fallbacks if a key is missing).

#### `[test]` – hypothesis test controls

| Option | Description | Default (config.txt) |
| --- | --- | --- |
| `alpha` | Significance level used for bootstrap confidence intervals and p-values. | `0.05` |
| `bootstrapping iterations` | Number of bootstrap resamples used when estimating percentile distributions. | `600` |
| `sample` | Target sample size taken from cleaned inputs before bootstrapping (falls back to 10,000 if omitted). | `2000` |
| `threshold` | Threshold value for single-sample comparisons; required when only one CSV is provided. | `1000` |
| `percentile` | Percentile to analyse (validated between 1–99; defaults to 95 when absent). | `95` |

#### `[input]` – data cleaning and validation

| Option | Description | Default (config.txt) |
| --- | --- | --- |
| `outlier threshold` | Upper bound applied during cleaning; values above this are dropped. | `2500` |
| `lower threshold` | Lower bound applied during cleaning; values below this are dropped. | `100` |
| `minimum sample size` | Minimum number of observations required per input; warns and exits early below this threshold (falls back to 500). | `500` |
| `validate_ratio_scale` | Enforce ratio-scale checks (non-negative, non-binary) before analysis. | `True` |

#### `[output]` – result fields and artefacts

| Option | Description | Default (config.txt) |
| --- | --- | --- |
| `create_log` | Write debug logs to `tool.log`. | `True` |
| `p95_1`, `p95_2` | Include bootstrapped percentile means for sample 1 and 2. | `True` |
| `ci lower p95_1`, `ci upper p95_1`, `ci lower p95_2`, `ci upper p95_2` | Emit percentile confidence interval bounds. | `True` |
| `p95_1_moe`, `p95_2_moe` | Emit margin of error (%) for each percentile estimate. | `True` |
| `p-value`, `alpha`, `sample size`, `significant difference`, `threshold` | Core hypothesis test statistics. | `True` |
| `data source` | Include the path of sampled inputs when empirical percentiles are requested. | `False` |
| `p95_1_empirical`, `p95_2_empirical` | Output empirical percentile calculations alongside bootstrap results. | `False` |
| `p90_1`, `p90_2`, `ci lower p90_1`, `ci upper p90_1`, `ci lower p90_2`, `ci upper p90_2`, `p90_1_moe`, `p90_2_moe`, `p90_1_empirical`, `p90_2_empirical` | Optional P90 counterparts for the above fields. | `False` |
| `histogram`, `histogram_log_scale`, `boxplot`, `kde_plot` | Generate diagnostic plots (log scaling only applies when `histogram = True`). | `False` |

#### `[descriptive analysis]` – summary statistics and diagnostics

| Option | Description | Default (config.txt) |
| --- | --- | --- |
| `required` | Run descriptive analysis before hypothesis testing. | `True` |
| `descriptive only` | Skip hypothesis testing and only emit descriptive results. | `False` |
| `mean`, `median`, `min`, `max`, `sample size`, `standard deviation`, `skewness`, `mode` | Toggle individual descriptive statistics. | `True` for `mean`, `min`, `max`, `sample size`, `standard deviation`; `False` otherwise |
| `p95_empirical` | Include an empirical P95 in the descriptive output. | `False` |
| `diagraming` | Enable plot generation during descriptive analysis (uses `output` plot toggles). | `False` |
| `unimodality_test_enabled` | Require unimodality checks before sampling; when `False`, the CLI skips these guards. | `False` |
| `bandwidth` | Bandwidth strategy passed to the KDE used in unimodality checks. | `silverman` |
| `get extended report` | Add unimodality diagnostics (peak count, dip test p-value, etc.) to the descriptive results. | `False` |

#### `[clean]` – temporary file handling

| Option | Description | Default (config.txt) |
| --- | --- | --- |
| `clean_all` | Remove intermediate cleaned/sampled CSVs after the run completes. | `True` |

#### `[interpretation]` – narrative output

| Option | Description | Default (config.txt) |
| --- | --- | --- |
| `explain the result` | Produce a textual interpretation after results are generated. | `True` |
| `use_chatgpt_api` | Use the OpenAI Chat Completions API for richer narratives (requires an API key). | `False` |
| `save the results into file` | Persist interpretation Markdown to `interpretation.md` instead of printing to stdout. | `True` |
| `openai_api_key` | API key used when `use_chatgpt_api = True`; leave blank to rely on environment variables. | *(empty)* |

`kw-permutation` parameters are passed directly as CLI flags (`--permutations`, `--seed`, `--report`, `--summary-csv`, `--quiet`); they are not stored in `config.txt`.

### Cleaning up

When `[clean] clean_all = True`, temporary cleaned and sampled CSV files are removed after the CLI finishes to keep the workspace tidy ([smart_comp/cli/app.py](smart_comp/cli/app.py#L155-L160)).

## Running tests

Execute the unit tests with `pytest` from the repository root:

```bash
pytest
```

The suite covers CLI argument parsing, file cleanup, and key analytical helpers.

## Troubleshooting

- Ensure your CSV inputs contain a single column of numeric values with no header row.
- If the CLI exits early with ratio scale or sample size errors, adjust the `[input] minimum sample size` or confirm the data meets the expected scale.
- Set `[output] create_log = True` to collect detailed run logs in `tool.log` for debugging ([config.txt](config.txt#L17-L21)).

## License

This repository currently does not include an explicit license. Please consult the project maintainers before using it in production environments.
