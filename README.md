# HCDT: Human-Centered Digital Twin for Multihazard Research

Research project for the GSC mini-conference research challenge. This repository provides a human-centered digital twin (HCDT) framework for multihazard analysis, combining NHERI DesignSafe data with spatial and network modeling.

## Quickstart

```bash
git clone https://github.com/KurtSoncco/NHERI_competition_2026.git
cd NHERI_competition_2026
./scripts/bootstrap_env.sh
source .venv/bin/activate
```

Then open `notebooks/00_quickstart.ipynb` in Jupyter.

## Data Setup

Data must be downloaded manually from [DesignSafe](https://www.designsafe-ci.org):

- **PRJ-2113** (Michael)
- **PRJ-5770** (Ian-BD)

Place downloaded data under `data/raw/` (this folder is git-ignored).

## Development

### Environment (uv)

1. Sync environment (creates `.venv` and installs deps):
   ```bash
   uv sync --extra dev
   ```

2. Activate venv:
   ```bash
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   ```

### Project Structure

```
src/hcdt/           # Main package (HCDT = human-centered digital twin)
  data/             # Data loading & preprocessing
  dtwin/            # Digital twin modeling
  analysis/         # Analysis & visualization
notebooks/          # Jupyter notebooks
tests/              # Pytest tests
scripts/            # Utility scripts
```

### License

MIT License. See [LICENSE](LICENSE) for details.
