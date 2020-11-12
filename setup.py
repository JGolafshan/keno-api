from setuptools import setup


def readme():
    with open('README.md') as f:
        return f.read()


setup(name='keno-api',
      version='0.1',
      description='Unofficial Keno API - For Australia',
      long_description=readme(),
      url='https://github.com/JGolafshan/KenoAPI',
      author='Joshua David Golafshan',
      author_email='NAN',
      license='Unlicense Licensei',
      install_requires=[
          'datetime',
          'pandas',
          'requests',
          'math',
      ],
      scripts=[],
      keywords='keno keno-api australia ',
      packages=['grandmasomsri'],
      package_dir={'keno-api': 'src/keno'},
      package_data={'': ['']
                    },
      )
