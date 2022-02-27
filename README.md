# Wordle

My implementation of https://www.powerlanguage.co.uk/wordle/

## Installation

Make a [virtual env](https://docs.python.org/3/tutorial/venv.html) and then run
`pip install -e .`

## wordle

This is the _"game engine"_.

* `wordle --help` for a few options
* `wordle` and follow the prompts.
* `wordle word` to force a word instead of a random one.

## solver

This will make suggestions to help solve a wordle puzzle interactively
when the word is not known, or it can show the steps of solving a puzzle
if the word is already known.

* `solver` follow the prompts
* `solver the_word` to automate finding the given word
* `solver --first` make a suggestion for the first word and exit
* `solver --count` show letter distributions and exit

Inputting the server response is kinda crappy.

* `i` letter is _In_ the word
* `o` letter is _Out_ of the word
* `e` letter is in the _Exact_ spot

## interactive

This overly complicated tui allow you type in patterns and shows matching words,
it's a real time grep. One use is to run with `-i` for invisible mode, this just
shows word counts without showing the words themselves. This is useful to test
a hypothesis such as _"I think the second letter is an i and ends with a t"_.

Type `.` as a wildcard, type `!c` to exclude the letter `c`.

* `-e letters` if you already know some letters to exclude
* `-i` invisible mode
