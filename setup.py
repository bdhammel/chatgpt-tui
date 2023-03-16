import pathlib

from setuptools import setup, find_packages

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / 'README.md').read_text()

# This call to setup() does all the work
setup(
    name="aitui",
    version="0.0.1",
    description="",
    long_description=README,
    long_description_content_type="text/markdown",
    url="",
    author="Ben Hammel",
    author_email="bdhammel@gmail.com",
    license="MIT",
    install_requires=(HERE / "requirements.txt").read_text().splitlines(),
    entry_points={
        'console_scripts': ['ai=ai.cli:main'],
    },
    packages=find_packages(),
    include_package_data=True
)
