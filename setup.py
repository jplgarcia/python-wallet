from setuptools import setup, find_packages

setup(
    name="cartesi_wallet",
    version="0.0.4",
    packages=find_packages(),
    install_requires=[
        "cytoolz>=0.12.2",
        "requests>=2.31.0",
        "eth_abi>=4.0.0",
        "routes>=2.5.0"
    ],
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    )