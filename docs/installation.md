# Installation

## From PyPI

```bash
pip install compas_nest
```

To visualize results, also install the viewer:

```bash
pip install compas_viewer
```

## From source

Requires a C++17/20 compiler (MSVC on Windows, clang on macOS, gcc/clang on Linux) and CMake ≥ 3.15.
The OpenNest C++ engine sources are a git submodule under `external/nest/` (self-contained — Clipper2
and a minimal Boost subset are bundled, so no CGAL/Boost/Eigen download is needed).

### One step (uv — macOS, Windows Git Bash, Linux)

Creates a local `.venv`, installs every dependency, and builds the package:

```bash
git clone --recurse-submodules https://github.com/petrasvestartas/compas_nest.git
cd compas_nest
bash bash/install.sh
```

After editing C++ sources, rebuild without recreating the env: `bash bash/build.sh --test`.

### conda

```bash
conda env create -f environment.yml
conda activate compas_nest
pip install --no-build-isolation -ve .
```

### plain pip (editable)

```bash
git clone --recurse-submodules https://github.com/petrasvestartas/compas_nest.git
cd compas_nest
pip install nanobind "scikit-build-core[pyproject]"
pip install --no-build-isolation -ve .
```
