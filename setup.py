DESCRIPTION = """pykechain is a an open source Python API to KE-chain.
Provide remote access and control through the public KE-chain API. Works only
in combination with a valid KE-chain license. KE-works BV (c) 2016 """

# Always prefer setuptools over distutils
from setuptools import setup, find_packages

# To use a consistent encoding
from codecs import open
from os import path

PACKAGE_NAME = "pykechain"
HERE = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(HERE, "README.rst"), encoding="utf-8") as f:
    long_description = f.read()

ABOUT = {}
with open(path.join(HERE, PACKAGE_NAME, "__about__.py")) as f:
    exec(f.read(), ABOUT)

setup(
    name=ABOUT["name"],
    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version=ABOUT["version"],
    description=ABOUT["description"],
    long_description=long_description,
    long_description_content_type="text/x-rst",
    # The project's main homepage.
    url="https://github.com/KE-works/pykechain",
    # Author details
    author=ABOUT["author"],
    author_email=ABOUT["email"],
    # Choose your license
    license="Apache Open Source License 2.0",
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        "Development Status :: 5 - Production/Stable",
        # Indicate who your project is intended for
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
        "Topic :: Scientific/Engineering",
        # Pick your license as you wish (should match "license" above)
        "License :: OSI Approved :: Apache Software License",
        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: Implementation :: PyPy",
        # OS
        "Operating System :: MacOS",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
    ],
    # What does your project relate to?
    keywords="python api rest sdk KE-chain",
    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=find_packages(exclude=["tests", "tests.*"]),
    # Project URLs
    project_urls={
        "Documentation": "https://pykechain.readthedocs.io/en/latest",
        "Changelog": "https://github.com/KE-works/pykechain/blob/master/CHANGELOG.rst",
        "Source": "https://github.com/KE-works/pykechain/",
        "Tracker": "https://github.com/KE-works/pykechain/issues",
        "Company Page": "https://ke-chain.com",
    },
    # Alternatively, if you want to distribute just a my_module.py, uncomment
    # this:
    #   py_modules=["my_module"],
    # List run-time dependencies here.  These will be installed by pip when
    # your project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=[
        "requests>=2.20.0",
        "envparse",
        "typing",
        "six",
        "jsonschema",
        "semver>=2.10.0",
        "pytz",
    ],
    setup_requires=["pytest-runner", "wheel"],
    tests_require=["pytest", "betamax"],
    python_requires=">=3.7",
    # If there are data files included in your packages that need to be
    # installed, specify them here.  If using Python 2.6 or less, then these
    # have to be included in MANIFEST.in as well.
    package_data={
        "pykechain": ["py.typed"],
    },
    # Although 'package_data' is the preferred approach, in some case you may
    # need to place data files outside of your packages. See:
    # http://docs.python.org/3.4/distutils/setupscript.html#installing-additional-files # noqa
    # In this case, 'data_file' will be installed into '<sys.prefix>/my_data'
    # data_files=[('my_data', ['data/data_file'])],
    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
    # entry_points={
    #     'console_scripts': [
    #         'sample=sample:main',
    #     ],
    # },
)
