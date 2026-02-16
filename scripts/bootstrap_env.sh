#!/usr/bin/env bash
# Bootstrap development environment for HCDT.
set -e
cd "$(dirname "$0")/.."
uv sync --extra dev
echo "Environment ready. Activate with: source .venv/bin/activate"
