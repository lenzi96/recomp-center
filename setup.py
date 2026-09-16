from setuptools import setup, find_packages

setup(
    name="recomp-center",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "PyQt6>=6.4.0",
    ],
    entry_points={
        "console_scripts": [
            "recomp-center=recomp_center.app:main",
        ],
    },
)
