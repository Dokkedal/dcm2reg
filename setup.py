# --- Setup file to let pip know what to install --- #

import setuptools
from docs.source.conf import version, author

with open("README.rst", "r") as f:
    long_desc = f.read()

with open("requirements.txt", "r") as f:
    install_reqs = f.readlines()

setuptools.setup(
    name = "dcm2reg",
    version = version,
    author = author,
    description = "medical image preprocessing package",
    long_description = long_desc,
    long_description_content_type = "text/reStructuredText",
    url = https://github.com/Dokkedal/dcm2reg,
    license = "MIT",
    packages = ["dcm2reg"],
    install_requires = install_reqs
)
