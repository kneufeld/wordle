#!/usr/bin/env python

import pathlib
import argparse
import re
import collections
import itertools
import readline
import random

from .utils import dotdict

class Wordle:

    LETTER_IN    = 'i' # in, in word but wrong spot
    LETTER_OUT   = 'o' # out, not in word
    LETTER_EXACT = 'e' # exact spot

    def __init__(self, args):
        args = dotdict(args)
        self.args = args
        self.wordlen = args.wordlen
        self.words = self.read_dict(args.dict, self.wordlen)

    @property
    def words(self):
        """
        current subset of dictionary words that could be solution
        """
        return self._words

    @words.setter
    def words(self, dictionary):
        self._words = dictionary

    @property
    def length(self):
        return len(self.words)

    @classmethod
    def response_set(cls):
        return set([
            cls.LETTER_IN,
            cls.LETTER_OUT,
            cls.LETTER_EXACT,
        ])

    @classmethod
    def read_dict(cls, dictfile, wordlen):
        words = set()

        dictionary = dictfile.open().read().splitlines()
        print(f"starting dictionary contains {len(dictionary)} words")

        for word in dictionary:
            if all([
                len(word) == wordlen,       # 5 letters long
                # turns out you can have repeat letters
                # len(set(word)) == wordlen,  # 5 unique letters, not the same as above, eg. otter
                word == word.lower()        # no capitals
            ]):
                words.add(word)

        # logger.debug(f"our word list contains {len(words)}, {wordlen} letter words")
        return words

    def check_word(self, word, guess):
        """
        return a response for the given guess
        """

        resp = ''

        for i in range(self.wordlen):
            if guess[i] == word[i]:
                resp += self.LETTER_EXACT
            elif guess[i] in word:
                resp += self.LETTER_IN
            else:
                resp += self.LETTER_OUT

        return resp
