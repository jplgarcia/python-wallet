from setuptools import setup, find_packages

setup(
    name="coil_wallet",
    version="0.0.4",
    packages=find_packages(),
    install_requires=[
        "requests>=2.31.0",
        "routes>=2.5.0"
    ],
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    )