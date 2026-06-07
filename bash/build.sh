#!/usr/bin/env bash
#
# Rebuild compas_nest in the existing .venv after editing C++ sources, without
# recreating the environment. Works on macOS and Windows (Git Bash).
#
#   bash bash/build.sh            # rebuild only
#   bash bash/build.sh --test     # rebuild, then run pytest
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT"

case "$(uname -s)" in
    MINGW*|MSYS*|CYGWIN*) OS=windows ;;
    *) OS=other ;;
esac

if [ "$OS" = "windows" ]; then
    VENV_PY="$ROOT/.venv/Scripts/python.exe"
else
    VENV_PY="$ROOT/.venv/bin/python"
fi

if [ ! -x "$VENV_PY" ] && [ ! -f "$VENV_PY" ]; then
    echo "ERROR: .venv not found. Run 'bash bash/install.sh' first."
    exit 1
fi

echo ">> Rebuilding compas_nest (editable) ..."
if [ "$OS" = "windows" ]; then
    VSW="C:/Program Files (x86)/Microsoft Visual Studio/Installer/vswhere.exe"
    if [ -f "$VSW" ]; then
        VSMAJOR="$("$VSW" -latest -property installationVersion 2>/dev/null | cut -d. -f1)"
        case "$VSMAJOR" in
            17) export CMAKE_GENERATOR="Visual Studio 17 2022" ;;
            16) export CMAKE_GENERATOR="Visual Studio 16 2019" ;;
            15) export CMAKE_GENERATOR="Visual Studio 15 2017" ;;
        esac
        export CMAKE_GENERATOR_PLATFORM=x64
    fi
fi
uv pip install --python "$VENV_PY" --no-build-isolation -ve .

if [ "${1:-}" = "--test" ]; then
    echo ">> Running tests ..."
    "$VENV_PY" -m pytest tests/ -q
fi

echo ">> Done."
