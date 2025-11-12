# How to build and publish this project to PyPI / TestPyPI

This project is prepared to be built with setuptools (pyproject.toml + setup.cfg present).

Important assumptions and notes
- I added packaging metadata with a default version `0.1.0`.
- I set the package name to `desafio-mba-fc-01`. Confirm if you prefer a different name (e.g. using underscores for import name).
- I assumed an MIT license in `setup.cfg`; change if needed.

Recommended quick workflow (PowerShell on Windows)

1) Create and activate a virtual environment (optional but recommended)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2) Install build tools

```powershell
pip install --upgrade pip
pip install --upgrade build twine
```

3) Build distributions

```powershell
python -m build
```

This creates `dist/` containing a source archive and a wheel.

4) (Optional, recommended) Upload to TestPyPI first

Create an account at https://test.pypi.org/ and then run:

```powershell
twine upload --repository testpypi dist/*
```

5) Upload to PyPI

Create a PyPI account and then run:

```powershell
twine upload dist/*
```

Notes on authentication
- Twine will prompt for username/password. You can also use an API token (recommended) and put it into `~/.pypirc` or supply `TWINE_USERNAME`/`TWINE_PASSWORD` env vars.

Post-publish
- Tag the release in git and create a GitHub Release (optional):

```powershell
git tag v0.1.0
git push origin v0.1.0
```

If you want, I can:
- Run the build locally and report results
- Attempt an upload to TestPyPI (I will need your TestPyPI credentials or an API token)
- Change the package name/version/license to your preference
