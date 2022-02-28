from setuptools import setup

# install with: pip install -e .

setup(
    name='wordle',
    version='0.1.0',
    py_modules=['lib'],
    install_requires=[
        'click',
        'rich',
        'urwid',
        'blinker',
    ],
    entry_points={
        'console_scripts': [
            'wordle = lib.wordleui:cli',
            'solver = lib.solverui:cli',
            'reverser = lib.reverseui:cli',
            'interactive = lib.interactive:cli',
        ],
    },
)
