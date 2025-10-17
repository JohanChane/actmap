from setuptools import setup, find_packages

setup(
    name="actmap",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "click>=8.0.0",
        "tomli-w>=1.0.0",
    ],
    entry_points={
        'console_scripts': [
            'actmap=actmap.cli:cli',
            'actmap-generate=pkg_actmap.generate_config:generate_config',
            'actmap-execute=pkg_actmap.execute:execute',
        ],
    },
    python_requires=">=3.7",
)