#!/usr/bin/env bash
#
# Create a local uv virtual environment (.venv), install all dependencies, and
# build compas_nest in editable mode. Works on macOS and on Windows (run from
# Git Bash). Linux works too.
#
#   bash bash/install.sh
#
# Options (environment variables):
#   PYTHON_VERSION   Python to use for the venv (default: 3.12)
#
set -euo pipefail

# --- locate the repo root (parent of this bash/ folder) ---------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT"

PYTHON_VERSION="${PYTHON_VERSION:-3.12}"

# --- detect OS --------------------------------------------------------------
case "$(uname -s)" in
    Darwin*) OS=mac ;;
    Linux*)  OS=linux ;;
    MINGW*|MSYS*|CYGWIN*) OS=windows ;;
    *) OS=unknown ;;
esac
echo ">> Platform: $OS   Python: $PYTHON_VERSION"

# --- require uv -------------------------------------------------------------
if ! command -v uv >/dev/null 2>&1; then
    echo "ERROR: 'uv' is not installed or not on PATH."
    if [ "$OS" = "windows" ]; then
        echo "  Install it with:  powershell -c \"irm https://astral.sh/uv/install.ps1 | iex\""
    else
        echo "  Install it with:  curl -LsSf https://astral.sh/uv/install.sh | sh"
    fi
    exit 1
fi

# --- make sure the C++ engine submodule is present --------------------------
if [ -f .gitmodules ]; then
    echo ">> Initialising git submodules (external/nest) ..."
    git submodule update --init --recursive
fi
if [ ! -f external/nest/nest_physics_cpp/nest_physics_capi.cpp ]; then
    echo "ERROR: C++ engine sources missing at external/nest. Submodule init failed?"
    exit 1
fi

# --- create the virtual environment -----------------------------------------
echo ">> Creating uv virtual environment in .venv ..."
uv venv --python "$PYTHON_VERSION" .venv

if [ "$OS" = "windows" ]; then
    VENV_PY="$ROOT/.venv/Scripts/python.exe"
else
    VENV_PY="$ROOT/.venv/bin/python"
fi

# --- install dependencies (build + runtime + viewer + tests) ----------------
echo ">> Installing dependencies into .venv ..."
uv pip install --python "$VENV_PY" \
    nanobind>=2.12 \
    "scikit-build-core[pyproject]>=0.10" \
    cmake>=3.15 \
    ninja \
    "numpy>=1.24" \
    "compas>=2.15,<3" \
    compas_viewer \
    pytest \
    ruff

# --- build + install compas_nest (editable) ---------------------------------
echo ">> Building compas_nest (editable) ..."
if [ "$OS" = "windows" ]; then
    # Use the Visual Studio CMake generator: MSBuild locates the MSVC toolchain
    # itself, so no vcvars / 'cmd' wrapper is needed (which is fragile from Git Bash).
    VSW="C:/Program Files (x86)/Microsoft Visual Studio/Installer/vswhere.exe"
    if [ -f "$VSW" ]; then
        VSMAJOR="$("$VSW" -latest -property installationVersion 2>/dev/null | cut -d. -f1)"
        case "$VSMAJOR" in
            17) export CMAKE_GENERATOR="Visual Studio 17 2022" ;;
            16) export CMAKE_GENERATOR="Visual Studio 16 2019" ;;
            15) export CMAKE_GENERATOR="Visual Studio 15 2017" ;;
        esac
        export CMAKE_GENERATOR_PLATFORM=x64
        echo ">> Using CMake generator: ${CMAKE_GENERATOR:-default}"
    fi
fi
uv pip install --python "$VENV_PY" --no-build-isolation -ve .

# --- verify -----------------------------------------------------------------
echo ">> Verifying import ..."
"$VENV_PY" -c "import compas_nest; from compas_nest import OpenNestCollision, OpenNest2; print('compas_nest', compas_nest.__version__, 'OK')"

echo ""
echo "Done. Activate the environment with:"
if [ "$OS" = "windows" ]; then
    echo "    source .venv/Scripts/activate      # Git Bash"
    echo "    .venv\\Scripts\\activate            # PowerShell/cmd"
else
    echo "    source .venv/bin/activate"
fi
echo "Run the tests with:   bash bash/build.sh --test   (or 'pytest tests/' once activated)"
