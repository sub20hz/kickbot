from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

with open("requirements.txt", "r") as f:
    requirements = f.read().splitlines()

setup(
    name="kickbot",
    version="0.0.5",
    license="MIT",
    python_requires=">=3.10",
    description="Package for developing kick.com bots",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/lukemvc/kickbot",
    packages=find_packages(),
    install_requires=requirements,
)
