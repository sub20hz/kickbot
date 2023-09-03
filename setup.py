from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="kickbot",
    version="0.0.1",
    description="Package for developing kick.com bots",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/lukemvc/kickbot",
    packages=find_packages(),
    install_requires=[
        'attrs==23.1.0',
        'certifi==2023.7.22',
        'charset-normalizer==3.2.0',
        'exceptiongroup==1.1.3',
        'h11==0.14.0',
        'idna==3.4',
        'outcome==1.2.0',
        'PySocks==1.7.1',
        'requests==2.31.0',
        'selenium==4.12.0',
        'sniffio==1.3.0',
        'sortedcontainers==2.4.0',
        'tls-client==0.2.1',
        'trio==0.22.2',
        'trio-websocket==0.10.3',
        'undetected-chromedriver==3.5.3',
        'urllib3==2.0.4',
        'websockets==11.0.3',
        'wsproto==1.2.0',
    ],
)
