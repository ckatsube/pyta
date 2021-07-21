from setuptools import setup


with open('README.md') as fh:
    long_description = fh.read()

setup(
    name='python-ta',
    version='1.8.0a2',
    description='Code checking tool for teaching Python',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='http://github.com/pyta-uoft/pyta',
    author='David Liu',
    author_email='david@cs.toronto.edu',
    license='MIT',
    packages=['python_ta', 'python_ta.reporters', 'python_ta.checkers',
              'python_ta.cfg', 'python_ta.contracts',
              'python_ta.patches',
              'python_ta.transforms', 'python_ta.typecheck', 'python_ta.util'],
    install_requires=[
        'astroid>=2.6,<2.7',
        'hypothesis',
        'pycodestyle',
        'pylint>=2.9,<2.10',
        'colorama',
        'six',
        'jinja2',
        'pygments',
        'wrapt>=1.12.0',
        'typeguard>=2.7.1',
        'requests',
        'click>=8.0.1',
        'Werkzeug>=2.0.1',
        'watchdog>=2.1.3'
    ],
    extras_require={
        'dev': [
            'graphviz',
            'inflection',
            'myst-parser',
            'pytest',
            'pytest-cov',
            'sphinx',
            'sphinx-rtd-theme'
        ]
    },
    entry_points={
        'console_scripts': [
            'python_ta = python_ta.__main__:main'
        ],
    },
    python_requires='~=3.8',
    include_package_data=True,
    zip_safe=False)
