"""Set up the aiovlc package."""
from pathlib import Path

from setuptools import find_packages, setup

DESCRIPTION = "A package for talking to vlc over its telnet interface using asyncio."

PROJECT_DIR = Path(__file__).parent.resolve()
README_FILE = PROJECT_DIR / "README.md"
LONG_DESCRIPTION = README_FILE.read_text(encoding="utf-8")
VERSION = (PROJECT_DIR / "aiovlc" / "VERSION").read_text().strip()

REQUIRES = [
    "click",
]

setup(
    name="aiovlc",
    version=VERSION,
    url="https://github.com/MartinHjelmare/aiovlc",
    author="Martin Hjelmare",
    author_email="marhje52@gmail.com",
    packages=find_packages(exclude=["contrib", "docs", "tests*"]),
    package_data={"aiovlc": ["py.typed"]},
    include_package_data=True,
    zip_safe=False,
    license="Apache-2.0",
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    python_requires=">=3.8",
    install_requires=REQUIRES,
    entry_points={"console_scripts": ["aiovlc = aiovlc.cli:cli"]},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Home Automation",
    ],
)
