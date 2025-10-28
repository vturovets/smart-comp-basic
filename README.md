# Smart-Comp

Smart-Comp is a command-line toolkit for statistically comparing the 95th percentile (P95) of one or two latency or performance datasets.  It automates data cleaning, bootstrapped hypothesis testing, and narrative interpretation so you can determine whether a regression or improvement is statistically significant.【F:smart_comp/cli/app.py†L1-L153】

## Features

- **Single or dual dataset comparisons** – compare a dataset against a fixed threshold or evaluate the difference between two CSV inputs using bootstrap resampling.【F:smart_comp/cli/app.py†L32-L116】
- **Descriptive statistics pipeline** – optional descriptive summaries (mean, min/max, standard deviation, etc.) generated from cleaned inputs.【F:smart_comp/cli/app.py†L59-L79】【F:smart_comp/io/output.py†L24-L39】
- **Automated data hygiene** – validates ratio-scale requirements, enforces guardrails, removes outliers, and writes sanitized copies of the inputs.【F:smart_comp/io/input.py†L10-L35】【F:smart_comp/validation/checks.py†L1-L69】
- **Autosized sampling** – derives sample sizes tailored to your data before running hypothesis tests.【F:smart_comp/cli/app.py†L82-L95】【F:smart_comp/sampling/autosize.py†L1-L34】
- **Result interpretation** – optional Markdown explanations and visualization call-outs help communicate findings to stakeholders.【F:smart_comp/cli/app.py†L117-L153】
- **Configurable outputs** – toggle log creation, text exports, histograms, KDE plots, and more from a simple INI configuration file.【F:config.txt†L1-L58】

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

Runtime dependencies – NumPy, pandas, SciPy, Matplotlib, diptest, and optional OpenAI APIs – are listed in `requirements.txt` alongside version pins.【F:requirements.txt†L1-L6】 For development work the test suite uses `pytest`.【F:requirements-dev.txt†L1-L2】

## Installation

1. Clone the project from the repo into local folder, and activate a virtual environment:

   ```bash
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

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

Run the CLI from the project root. The command accepts one or two CSV files plus an optional output path for the result summary.

```bash
python cli.py <input_1.csv> [input_2.csv] [results.txt]
```

- **Single input:** compares the dataset against the `[test] threshold` configured in `config.txt` and emits hypothesis test statistics for the sample P95.【F:smart_comp/cli/app.py†L46-L87】
- **Two inputs:** compares the P95 between the datasets using paired bootstrap resampling.【F:smart_comp/cli/app.py†L88-L115】
- **Output file:** if provided, the formatted results are written to disk; otherwise they are printed to stdout.【F:smart_comp/io/output.py†L8-L39】

By default the CLI will:

1. Clean and validate each CSV, ensuring a single numeric `value` column and applying outlier thresholds.【F:smart_comp/io/input.py†L10-L35】
2. Optionally produce descriptive statistics (`[descriptive analysis] required = True`).
3. Run unimodality checks (if enabled) before sampling.
4. Auto-sample cleaned data to the configured size and execute the bootstrap hypothesis test.【F:smart_comp/cli/app.py†L82-L109】
5. Save the results and (optionally) generate interpretation Markdown with links to any plots the configuration enables.【F:smart_comp/cli/app.py†L117-L153】

### Configuration

The CLI loads settings from `config.txt`. Tweak this file to control sampling, thresholds, cleaning rules, and output fields. Notable sections include:

- `[test]` – significance level, bootstrap iterations, sample size, and comparison threshold.
- `[input]` – outlier limits, minimum sample size, and ratio-scale enforcement.
- `[output]` – toggle individual statistics, diagnostics, log creation, and plot exports.
- `[descriptive analysis]` – enable descriptive runs, extended reports, and unimodality checks.
- `[interpretation]` – configure automatic narrative generation and persistence.【F:config.txt†L1-L73】

### Cleaning up

When `[clean] clean_all = True`, temporary cleaned and sampled CSV files are removed after the CLI finishes to keep the workspace tidy.【F:smart_comp/cli/app.py†L155-L160】

## Running tests

Execute the unit tests with `pytest` from the repository root:

```bash
pytest
```

The suite covers CLI argument parsing, file cleanup, and key analytical helpers.

## Troubleshooting

- Ensure your CSV inputs contain a single column of numeric values with no header row.
- If the CLI exits early with ratio scale or sample size errors, adjust the `[input] minimum sample size` or confirm the data meets the expected scale.
- Set `[output] create_log = True` to collect detailed run logs in `tool.log` for debugging.【F:config.txt†L17-L21】

## License

This repository currently does not include an explicit license. Please consult the project maintainers before using it in production environments.
