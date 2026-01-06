from setuptools import setup, Extension
from Cython.Build import cythonize

nios2_extension = Extension(
    name="pynios2",
    sources=["nios2.pyx"],
    libraries=["nios2"],
    library_dirs=["lib"],
    include_dirs=["lib"],
)

setup(
    name="pynios2",
    ext_modules=cythonize([nios2_extension]),
)
