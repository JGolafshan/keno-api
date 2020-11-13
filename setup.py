import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="keno-api",  # Replace with your own username
    version="0.0.2",
    author="Joshua David Golafshan",
    author_email="author@example.com",
    description="an educational package for educational uses only",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/JGolafshan/KenoAPI",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
