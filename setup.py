import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="keno-api",  # Replace with your own username
    version="0.0.17",
    author="Joshua David Golafshan",
    author_email="author@example.com",
    description="an educational package for educational uses only",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/JGolafshan/KenoAPI",
    packages=['src'],
    install_requires=[
        'datetime',
        'pandas',
        'requests',
    ],
    package_dir={'keno': 'src'},
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ]
)


"""
1: python setup.py sdist
2: twine upload --skip-existing dist/*

"""