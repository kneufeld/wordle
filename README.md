# Wordle

My implementation of https://www.powerlanguage.co.uk/wordle/

## Installation

The only dependency is `rich`, so therefore `pip install rich`.

## wordle.py

This is the _"game engine"_.

* `wordle.py --help` for a few options
* `wordle.py` and follow the prompts.
* `wordle.py word` to force a word instead of a random one.

## solver.py

This will make suggestions to help solve a wordle puzzle.

* `solver.py --first` make a suggestion for the first word and exit
* `solver.py` follow the prompts

Inputting the server response is granted a bit crappy.

* `i` letter is _In_ the word
* `o` letter is _Out_ of the word
* `y` _Yes_, the letter is in the exact spot
