import os
from setuptools import setup
from setuptools import Extension

from Cython.Build import cythonize

import numpy as np


ext_modules = [
    Extension(
        name='renderer',
        sources=['renderer.pyx'],
        include_dirs=[np.get_include()],
    )
]

setup(
    ext_modules=cythonize(
        ext_modules,
        annotate=True,
    ),
)

