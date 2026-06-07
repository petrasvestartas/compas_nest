cmake_minimum_required(VERSION 3.15...3.27)

project(nest_wrapper LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

# Static-link the MSVC runtime so the wheels carry no VC++ redistributable dependency.
if(POLICY CMP0091)
    cmake_policy(SET CMP0091 NEW)
endif()
if(MSVC)
    set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")
    add_compile_options(/Zm1000)
endif()

# ---------------------------------------------------------------------------
# Vendored OpenNest C++ engine sources (git submodule -> external/nest).
# No CGAL / Boost / Eigen download: both engines are self-contained.
# ---------------------------------------------------------------------------
set(NEST_DIR "${CMAKE_CURRENT_SOURCE_DIR}/external/nest")
set(PHYSICS_DIR "${NEST_DIR}/nest_physics_cpp")
set(NFP_DIR "${NEST_DIR}/opennest_cpp")

if(NOT EXISTS "${PHYSICS_DIR}/nest_physics_capi.cpp")
    message(FATAL_ERROR
        "OpenNest C++ sources not found at ${NEST_DIR}. "
        "Initialise the submodule: git submodule update --init --recursive")
endif()

# ---------------------------------------------------------------------------
# Python + nanobind
# ---------------------------------------------------------------------------
if(NOT SKBUILD)
    message(WARNING "This CMake file is meant to be driven by scikit-build-core "
                    "(pip install). Running it directly is unlikely to work.")
endif()

find_package(Python 3.9
    REQUIRED COMPONENTS Interpreter Development.Module
    OPTIONAL_COMPONENTS Development.SABIModule)

find_package(nanobind CONFIG REQUIRED)

# ===========================================================================
# Module 1: _nest_physics  (collision / overlap-relaxation engine)
#   Header-only solver; the C-API translation unit pulls it all in.
# ===========================================================================
nanobind_add_module(_nest_physics STABLE_ABI NB_STATIC
    src/_nest_physics.cpp
    "${PHYSICS_DIR}/nest_physics_capi.cpp")
target_include_directories(_nest_physics PRIVATE "${PHYSICS_DIR}")
if(NOT MSVC)
    target_compile_options(_nest_physics PRIVATE -O3)
endif()
install(TARGETS _nest_physics LIBRARY DESTINATION compas_nest)

# ===========================================================================
# Module 2: _nfp_nest  (NFP + genetic-algorithm engine)
#   Needs the vendored Clipper2 + nest_lib sources + the minimal Boost subset.
# ===========================================================================
set(NFP_SOURCES
    src/_nfp_nest.cpp
    "${NFP_DIR}/src/capi/nfp_nest_capi.cpp"
    "${NFP_DIR}/src/GeometryUtil.cpp"
    "${NFP_DIR}/src/MinkowskiConvolution.cpp"
    "${NFP_DIR}/src/NfpWorker.cpp"
    "${NFP_DIR}/src/GeneticAlgorithm.cpp"
    "${NFP_DIR}/src/NestingEngine.cpp"
    "${NFP_DIR}/src/NestingContext.cpp"
    "${NFP_DIR}/src/clipper2/clipper.engine.cpp"
    "${NFP_DIR}/src/clipper2/clipper.offset.cpp"
    "${NFP_DIR}/src/clipper2/clipper.rectclip.cpp")

nanobind_add_module(_nfp_nest STABLE_ABI NB_STATIC ${NFP_SOURCES})
target_include_directories(_nfp_nest PRIVATE
    "${NFP_DIR}/src"
    "${NFP_DIR}/third_party/boost_min")
if(MSVC)
    target_compile_definitions(_nfp_nest PRIVATE _USE_MATH_DEFINES)
    target_compile_options(_nfp_nest PRIVATE /wd4244 /wd4267 /wd4305)
else()
    target_compile_options(_nfp_nest PRIVATE -O3 -Wno-unused-parameter)
endif()
install(TARGETS _nfp_nest LIBRARY DESTINATION compas_nest)

# ===========================================================================
# Module 3: _clipper  (Clipper2 polygon offsetting for clearance)
#   Reuses the Clipper2 sources vendored with the NFP engine.
# ===========================================================================
nanobind_add_module(_clipper STABLE_ABI NB_STATIC
    src/_clipper.cpp
    "${NFP_DIR}/src/clipper2/clipper.engine.cpp"
    "${NFP_DIR}/src/clipper2/clipper.offset.cpp"
    "${NFP_DIR}/src/clipper2/clipper.rectclip.cpp")
target_include_directories(_clipper PRIVATE "${NFP_DIR}/src")
if(MSVC)
    target_compile_definitions(_clipper PRIVATE _USE_MATH_DEFINES)
    target_compile_options(_clipper PRIVATE /wd4244 /wd4267 /wd4305)
else()
    target_compile_options(_clipper PRIVATE -O3 -Wno-unused-parameter)
endif()
install(TARGETS _clipper LIBRARY DESTINATION compas_nest)
