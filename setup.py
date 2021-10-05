from setuptools import setup

from costflow import __VERSION__

with open("requirements.txt", "r") as f:
    install_requires = f.read().splitlines()

with open("README.md", "r", encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='costflow',
    version=__VERSION__,
    packages=['costflow'],
    package_data={'': ['costflow-parser.js']},
    url='https://github.com/stdioa/costflow',
    install_requires=install_requires,
    license='GPLv3',
    author='StdioA',
    author_email='stdioa@163.com',
    description='A Python implementation for costflow parser.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ]
)
