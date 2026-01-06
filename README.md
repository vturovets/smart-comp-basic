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

The CLI loads settings from `config.txt`. Adjust this file to control sampling, thresholds, cleaning rules, permutation parameters, descriptive metrics, and output fields. Every available option is listed below with defaults and example usage (see [config.txt](config.txt#L1-L83)):

#### `[test]`

| Option | Description | Default | Example |
| --- | --- | --- | --- |
| `alpha` | Significance level for hypothesis tests. | `0.05` | `alpha = 0.01` |
| `bootstrapping iterations` | Number of bootstrap resamples. | `600` | `bootstrapping iterations = 2000` |
| `sample` | Target sample size when auto-sampling cleaned inputs. | `2000` | `sample = 5000` |
| `threshold` | Cutoff used for single-sample comparisons. | `1000` | `threshold = 750` |
| `percentile` | Percentile to analyze (integer between 1 and 99). | `95` | `percentile = 90` |

#### `[input]`

| Option | Description | Default | Example |
| --- | --- | --- | --- |
| `outlier threshold` | Values above this boundary are dropped during cleaning. | `2500` | `outlier threshold = 5000` |
| `lower threshold` | Values below this boundary are dropped during cleaning. | `100` | `lower threshold = 0` |
| `minimum sample size` | Enforces a minimum number of rows before tests can run. | `500` | `minimum sample size = 1000` |
| `validate_ratio_scale` | Enable ratio-scale validation before analysis. | `True` | `validate_ratio_scale = False` |

#### `[output]`

| Option | Description | Default | Example |
| --- | --- | --- | --- |
| `create_log` | Write diagnostic logs to `tool.log`. | `True` | `create_log = False` |
| Statistic flags | Toggle visibility of individual fields in saved/printed output. | See below | `p95_1 = False` |
| Diagram exports | Enable visualizations. | See below | `histogram = True` |

- **Statistic flags (defaults shown):** `p95_1 = True`, `p95_2 = True`, `ci lower p95_1 = True`, `ci upper p95_1 = True`, `ci lower p95_2 = True`, `ci upper p95_2 = True`, `p95_1_moe = True`, `p95_2_moe = True`, `p-value = True`, `alpha = True`, `sample size = True`, `significant difference = True`, `threshold = True`, `data source = False`, `p95_1_empirical = False`, `p95_2_empirical = False`, `p90_1 = False`, `p90_2 = False`, `ci lower p90_1 = False`, `ci upper p90_1 = False`, `ci lower p90_2 = False`, `ci upper p90_2 = False`, `p90_1_moe = False`, `p90_2_moe = False`, `p90_1_empirical = False`, `p90_2_empirical = False`.\n+- **Diagram exports (defaults shown):** `histogram = False`, `histogram_log_scale = False`, `boxplot = False`, `kde_plot = False` (enable any to generate the corresponding plot).\n+\n+#### `[descriptive analysis]`\n+\n+| Option | Description | Default | Example |\n+| --- | --- | --- | --- |\n+| `required` | Run the descriptive pipeline before hypothesis testing. | `True` | `required = False` |\n+| `descriptive only` | Skip hypothesis tests and emit only descriptive summaries. | `False` | `descriptive only = True` |\n+| Metric flags | Control which statistics appear. | See below | `skewness = True` |\n+| `diagraming` | Allow descriptive analysis to trigger `[output]` diagrams. | `False` | `diagraming = True` |\n+| `unimodality_test_enabled` | Run KDE-based unimodality checks before sampling. | `False` | `unimodality_test_enabled = True` |\n+| `bandwidth` | Bandwidth selection rule for unimodality KDE analysis. | `silverman` | `bandwidth = scott` |\n+| `get extended report` | Include extended unimodality diagnostics. | `False` | `get extended report = True` |\n+\n+- **Metric flags (defaults shown):** `mean = True`, `median = False`, `min = True`, `max = True`, `sample size = True`, `standard deviation = True`, `skewness = False`, `mode = False`, `p95_empirical = False`.\n+\n+#### `[clean]`\n+\n+| Option | Description | Default | Example |\n+| --- | --- | --- | --- |\n+| `clean_all` | Remove temporary cleaned and sampled CSV files after execution. | `True` | `clean_all = False` |\n+\n+#### `[interpretation]`\n+\n+| Option | Description | Default | Example |\n+| --- | --- | --- | --- |\n+| `explain the result` | Generate narrative interpretations of the statistics. | `True` | `explain the result = False` |\n+| `use_chatgpt_api` | Enable ChatGPT-powered interpretations (requires an API key). | `False` | `use_chatgpt_api = True` |\n+| `save the results into file` | Persist interpretation text to disk. | `True` | `save the results into file = False` |\n+| `openai_api_key` | API key used when `use_chatgpt_api` is enabled (falls back to `OPENAI_API_KEY`). | *(blank)* | `openai_api_key = sk-...` |\n+\n+`kw-permutation` options are primarily specified on the command line; provide `--permutations`, `--seed`, `--report`, and `--summary-csv` flags to tailor the permutation test outputs per run.

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
