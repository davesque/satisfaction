#!/usr/bin/env python

from setuptools import setup

extras_require = {
    "test": [
        "pytest",
        "pytest-cov",
    ],
    "lint": [
        "ruff",
        "black",
        "pyright",
        "pynvim",
    ],
    "dev": [
        "ipython",
        "ipdb",
    ],
}

extras_require["dev"] += extras_require["test"] + extras_require["lint"]


setup(
    name="satellite",
    version="0.1.0",
    python_requires=">=3.12",
    extras_require=extras_require,
    packages=["satellite"],
)
