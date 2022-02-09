#!/usr/bin/env python

import pathlib
import argparse
import re
import collections
import itertools
import readline
import random

from rich.console import Console
print = Console(color_system='truecolor').print

class Wordle:

    LETTER_IN    = 'i' # in, in word but wrong spot
    LETTER_OUT   = 'o' # out, not in word
    LETTER_EXACT = 'y' # yes, exact spot

    def __init__(self, args):
        self.args = args
        self.wordlen = args.len
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

    def pick_word(self, words):
        # can't random.choice from a set so use this hack
        return random.sample(words, 1)[0]

    def check_word(self, guess):
        """
        return a response for the given guess
        """

        assert self.word, "you need to set/pick a word first"

        resp = ''

        for i in range(self.wordlen):
            if guess[i] == self.word[i]:
                resp += self.LETTER_EXACT
            elif guess[i] in self.word:
                resp += self.LETTER_IN
            else:
                resp += self.LETTER_OUT

        return resp


class WordleUI:

    LETTER_IN    = "[bold dark_goldenrod]◼[/bold dark_goldenrod]"
    LETTER_OUT   = "[grey]◼[/grey]"
    LETTER_EXACT = "[green]◼[/green]"

    def __init__(self, wordle):
        self.wordle = wordle
        self.rounds = [] # [guess, response]

    @property
    def args(self):
        return self.wordle.args

    def validate_guess(self, word):
        if len(word) != self.wordle.wordlen:
            return "wrong word length"

        if word not in self.wordle.words:
            return "word not in dictionary"

        return None

    def get_guess(self):

        while True:
            word = input("what's your guess: ")
            word = word.lower()

            if reason := self.validate_guess(word):
                print(f"invalid guess: {reason}")
                continue

            return word

    def print_response(self, resp):
        for c in resp:
            if c == Wordle.LETTER_IN:
                print(WordleUI.LETTER_IN, end=' ')
            elif c == Wordle.LETTER_OUT:
                print(WordleUI.LETTER_OUT, end=' ')
            elif c == Wordle.LETTER_EXACT:
                print(WordleUI.LETTER_EXACT, end=' ')
            else:
                print(f"unknown letter in response: {c}")
        print()

    def print_guess(self, guess):
        for c in guess:
            print(c, end=' ')
        print()

    def show_round(self, round):

        guess = round[0]
        resp = round[1]

        self.print_response(resp)
        self.print_guess(guess)

    def show_rounds(self):

        for round in self.rounds:
            self.show_round(round)

    def show_summary(self):
        for _guess, resp in self.rounds:
            self.print_response(resp)
        print()

    def play(self):

        if self.args.start_word:
            self.wordle.word = self.args.start_word
            print(f"using given word: {self.args.start_word}")
        else:
            self.wordle.word = self.wordle.pick_word(self.wordle.words)
            print("I picked a word, what's your guess?")

        for i in range(6):
            guess = self.get_guess()
            resp = self.wordle.check_word(guess)

            self.rounds.append([guess, resp])
            self.show_rounds()

            if resp == 'y' * self.wordle.wordlen:
                print(f"[bold green]You got it in {len(self.rounds)} tries![/bold green]")
                self.show_summary()
                return

        print(f"[bold yellow]You ran out of tries. The word was: [blue]{self.wordle.word}[/blue][/bold yellow]")
        self.show_summary()


def main(args):

    try:
        wordle = Wordle(args)
        ui = WordleUI(wordle)
        ui.play()
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='wordle solver')
    #parser.add_argument('--dict', default='/usr/share/dict/words', type=pathlib.Path)
    parser.add_argument('--dict', default='words5.txt', type=pathlib.Path)
    parser.add_argument('--len', default=5)
    parser.add_argument('start_word', nargs='?', help="use this word instead of a random one")
    args = parser.parse_args()

    main(args)
