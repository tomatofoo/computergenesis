from setuptools import setup
from setuptools import Extension

from Cython.Build import cythonize


ext_modules = [
    Extension(
        name='pathfind',
        sources=['pathfind.pyx'],
    )
]

setup(
    ext_modules=cythonize(
        ext_modules,
        annotate=True,
    ),
)

