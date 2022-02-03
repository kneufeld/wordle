import pathlib
import re

dictfile = pathlib.Path('/usr/share/dict/words')
wordlen = 5

import logging
logger = logging.getLogger()

def read_dict(dictfile, wordlen):
    words = set()

    dictionary = dictfile.open().read().splitlines()
    logger.debug(f"dictionary contains {len(dictionary)} words")

    for word in dictionary:
        if all([
            len(word) == wordlen,       # 5 letters long
            len(set(word)) == wordlen,  # 5 unique letters
            word == word.lower()        # no capitals
        ]):
            words.add(word)

    logger.debug(f"our word list contains {len(words)}, {wordlen} letter words")
    return words

def parse_guess(guess):
    slots, *letters = guess.split(',')
    letters = letters[0] if letters else ''

    if len(slots) == 0:         # if guess = ',abc'
        slots = '.' * wordlen

    return slots, letters

def find_matches(words, guess):
    guesses = set()
    slots, letters = parse_guess(guess)

    slots = re.compile(slots)

    for word in words:
        if slots.match(word):
            for letter in letters:
                if letter not in word:
                    break
            else:
                guesses.add(word)

    return sorted(guesses)

