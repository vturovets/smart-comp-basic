# Building a `.whl` for `smart-comp-web`

This guide explains how to build a Python wheel (`.whl`) from this repository and use it in [`smart-comp-web`](https://github.com/vturovets/smart-comp-web).

## 1) Build the wheel in this repository

From the root of `smart-comp`:

```bash
python -m pip install --upgrade pip build
python -m build
```

After the build finishes, artifacts are created in `dist/`, for example:

- `dist/smart_comp-0.1.0-py3-none-any.whl`
- `dist/smart_comp-0.1.0.tar.gz`

## 2) (Recommended) Bump version before each release

If you are publishing a new build for `smart-comp-web`, update the version in `pyproject.toml` first:

```toml
[project]
version = "0.1.1"
```

Then rebuild:

```bash
python -m build
```

This avoids installing an older cached wheel with the same version.

## 3) Install the wheel in `smart-comp-web`

From the root of `smart-comp-web`:

```bash
python -m pip install /absolute/path/to/smart-comp/dist/smart_comp-0.1.0-py3-none-any.whl
```

If you use a virtual environment in `smart-comp-web`, activate it first.

## 4) Verify the installed version

In the `smart-comp-web` environment:

```bash
python -m pip show smart-comp
```

You should see the expected version and install location.

## 5) Typical update workflow

When making changes in `smart-comp` that should be used by `smart-comp-web`:

1. Update code in `smart-comp`.
2. Bump `version` in `pyproject.toml`.
3. Rebuild wheel (`python -m build`).
4. Reinstall wheel in `smart-comp-web` with the new file.
5. Restart the `smart-comp-web` app/server.

## Optional: install directly from a Git branch instead of a wheel

If your `smart-comp-web` workflow allows it, you can install directly from Git:

```bash
python -m pip install "git+https://github.com/vturovets/smart-comp.git@<branch-or-tag>"
```

Use the wheel approach when you want a fixed build artifact for repeatable deployments.
