from setuptools import setup
from setuptools import Extension

from Cython.Build import cythonize

import numpy as np


ext_modules = [
    Extension(
        name='camera',
        sources=['camera.pyx'],
        include_dirs=[np.get_include()],
    )
]

setup(
    ext_modules=cythonize(
        ext_modules,
        annotate=True,
    ),
)

