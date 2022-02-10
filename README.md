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

This will make suggestions to help solve a wordle puzzle interactively
when the word is not known, or it can show the steps of solving a puzzle
if the word is already known.

* `solver.py` follow the prompts
* `solver.py the_word` to automate finding the given word
* `solver.py --first` make a suggestion for the first word and exit

Inputting the server response is kinda crappy.

* `i` letter is _In_ the word
* `o` letter is _Out_ of the word
* `e` _Exact_, the letter is in the exact spot
