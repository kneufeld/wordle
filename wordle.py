#!/usr/bin/env python

import pathlib
import argparse
import re
import collections
import itertools
import readline

from rich.console import Console
print = Console(color_system='truecolor').print

class Wordle:

    LETTER_IN    = "[bold dark_goldenrod]◼[/bold dark_goldenrod]"
    LETTER_OUT   = "[grey]◼[/grey]"
    LETTER_EXACT = "[green]◼[/green]"

    def __init__(self, dpath, wordlen=5):
        self.console = Console(color_system='truecolor')
        # self.console.print(f"{Wordle.LETTER_IN} {Wordle.LETTER_OUT} {Wordle.LETTER_EXACT}")

        self.wordlen = wordlen
        self.words = self.read_dict(dpath, self.wordlen)
        self.iterations = [] # [guess, response]

    @property
    def words(self):
        """
        current subset of dictionary words that have could be solution
        """
        return self._words

    @words.setter
    def words(self, dictionary):
        self._words = dictionary

    @property
    def length(self):
        return len(self.words)

    def pick_word(self):
        import random
        return random.choice(list(self.words))

    def read_dict(self, dictfile, wordlen):
        words = set()

        dictionary = dictfile.open().read().splitlines()
        print(f"dictionary contains {len(dictionary)} words")

        for word in dictionary:
            if all([
                len(word) == wordlen,       # 5 letters long
                len(set(word)) == wordlen,  # 5 unique letters, not the same as above, eg. otter
                word == word.lower()        # no capitals
            ]):
                words.add(word)

        # logger.debug(f"our word list contains {len(words)}, {wordlen} letter words")
        return words

    def validate_guess(self, word):
        if len(set(word)) != self.wordlen:
            return "wrong word length"

        if word not in self.words:
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

    def print_response(self, r):
        if r == 'i':
            print(Wordle.LETTER_IN, end=' ')
        elif r == 'o':
            print(Wordle.LETTER_OUT, end=' ')
        elif r == 'y':
            print(Wordle.LETTER_EXACT, end=' ')

    def show_response(self, iteration):

        guess = iteration[0]
        resp = iteration[1]

        for r in resp:
            self.print_response(r)
        print()

        for c in guess:
            print(c, end=' ')
        print()

    def show_responses(self):

        for iteration in self.iterations:
            self.show_response(iteration)

    def make_response(self, guess):

        resp = ''

        for i in range(self.wordlen):
            if guess[i] == self.word[i]:
                resp += 'y'
            elif guess[i] in self.word:
                resp += 'i'
            else:
                resp += 'o'

        return resp

    def play(self):

        for i in range(6):
            guess = self.get_guess()
            resp = self.make_response(guess)

            self.iterations.append([guess, resp])
            self.show_responses()

            if resp == 'y' * self.wordlen:
                print(f"[bold green]You got it {len(self.iterations)} tries![/bold green]")
                return

        print(f"[bold yellow]You ran out of tries. The word was '{self.word}'[/bold yellow]")


def main(args):

    try:
        wordle = Wordle(args.dict, args.len)
        wordle.play()
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='wordle solver')
    #parser.add_argument('--dict', default='/usr/share/dict/words', type=pathlib.Path)
    parser.add_argument('--dict', default='words5.txt', type=pathlib.Path)
    parser.add_argument('--len', default=5)
    args = parser.parse_args()

    main(args)
