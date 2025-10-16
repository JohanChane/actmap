from setuptools import setup, find_packages

setup(
    name="actmap",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "click>=8.0.0",
    ],
    entry_points={
        'console_scripts': [
            'actmap=main:main',
        ],
    },
    python_requires=">=3.7",
)