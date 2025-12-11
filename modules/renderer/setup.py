from setuptools import setup
from setuptools import Extension

from Cython.Build import cythonize

ext_modules = [
    Extension(
        "renderer",
        sources=["renderer.pyx"],
    )
]

setup(
    ext_modules=cythonize(
        ext_modules,
        annotate=True,
    ),
)

