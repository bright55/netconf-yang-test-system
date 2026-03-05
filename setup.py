from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="yang-test-system",
    version="2.0.0",
    author="NETCONF/YANG Test System",
    author_email="",
    description="NETCONF/YANG Testing System based on RFC 6241/RFC 7950",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/bright55/netconf-yang-test-system",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "ncclient>=0.6.14",
        "pyang>=2.5.0",
        "pytest>=7.0.0",
        "jinja2>=3.0.0",
        "paramiko>=2.10.0",
        "requests>=2.28.0",
        "xmltodict>=0.13.0",
        "pyyaml>=6.0",
        "colorama>=0.4.6",
        "tabulate>=0.8.10",
    ],
    extras_require={
        "dev": [
            "pytest-cov>=3.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.950",
        ],
    },
    entry_points={
        "console_scripts": [
            "netconf-yang-test=yang_test_system.cli.main:main",
        ],
    },
)
