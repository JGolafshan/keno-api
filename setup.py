import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="kenoAPI",
    version="4.0.0",
    author="Joshua David Golafshan",
    description="Python-based API used to fetch real-time and historical data from the Australian Keno website.",
    # long_description=long_description,
    # long_description_content_type="text/markdown",
    url="https://github.com/JGolafshan/KenoAPI",
    keywords=["keno API", "keno", "algo", "algobetting", "API", "betting"],
    packages=["keno"],
    install_requires=[
        'datetime',
        'pandas',
        'requests',
    ],
    package_dir=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ]
)


"""
python setup.py sdist
python setup.py bdist_wheel

2: twine upload --skip-existing dist/*
"""