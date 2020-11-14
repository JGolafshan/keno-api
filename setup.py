import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="kenoAPI",
    version="1.0.5",
    author="Joshua David Golafshan",
    author_email="author@example.com",
    description="an educational package for educational uses only",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/JGolafshan/KenoAPI",
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