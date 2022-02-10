#!/usr/bin/env python

import pathlib
import argparse
import re
import collections
import itertools
import readline

Wordle = None

def import_wordle():
    # super hacky, read and parse wordle.py to get the Wordle class
    # so we can use its read_dict method. Gotta be DRY.
    l = {}
    exec(open('wordle.py').read(), {}, l)

    global Wordle
    Wordle = l['Wordle']

class Solver:

    def __init__(self, args):
        self.args = args
        self.wordlen = args.len
        self.words = self.read_dict(args.dict, self.wordlen)
        self.first = args.first
        self.letter_counts = self.count_letters(self.words)
        self.iteration = 0     # what attempt are we on
        self.pattern = ['.'] * self.wordlen

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

    def read_dict(self, dictfile, wordlen):
        return Wordle.read_dict(dictfile, wordlen)

    def count_letters(self, words):
        """
        count number of times each letter occurs in all words
        use set(word) since there are lots of fake words in the dict that skew
        the results, eg. esses
        """
        counts = collections.defaultdict(int)

        for word in words:
            for letter in set(word):
                counts[letter] += 1

        return counts

    def word_score(self, word):
        return sum([
            self.letter_counts[c] for c in set(word)
        ])

    def find_matches(self, exact, contains):
        """
        "exact" is a bit of a misnomer, it's anything or exact
        """
        matches = set()
        exact = re.compile(exact)
        excludes = [c for c, v in self.letter_counts.items() if v == 0]

        for word in self.words:
            if all([
                exact.match(word),
                all([c in word for c in contains]),
                not any([c in word for c in excludes])
            ]):
                matches.add(word)

        return matches

    def get_suggestions(self):
        """
        some hints of good words to the user
        """
        scored = dict([(word, self.word_score(word)) for word in self.words])
        top = sorted(scored.items(), key=lambda item: item[1], reverse=True)
        return top

    def validate_guess(self, word):
        if len(set(word)) != self.wordlen:
            return False

        return True

    def print_group(self, words, n=10):
        if not n:
            n = len(words)

        if isinstance(words, dict):
            words = list(words.items())

        for i, (k, v) in enumerate(itertools.groupby(words, key=lambda item: item[1])):
            if i >= n:
                break

            print(f"{k}: {', '.join([k for k, _ in v])}")

    def print_letter_counts(self):
        counts = self.count_letters(self.words)
        by_letter = sorted(counts.items())

        print("\nin alphabetical order:\n", end='')
        for l, c in by_letter:
            print(f"{l}: {c}", end=', ')
        print()

        # in count order
        by_count = sorted(counts.items(), key=lambda item: item[1], reverse=True)

        print("\nin numerical order:\n", end='')
        for l, c in by_count:
            print(f"{l}: {c}", end=', ')
        print()


    def get_guess(self):

        while True:
            word = input("what's your guess: ")
            word = word.lower()

            if not self.validate_guess(word):
                print("invalid guess, try again")
                continue

            return word

    def get_response(self):
        """
        ask user to type in response from wordle
        """
        print("i=letter in word (yellow), o=letter not in word (grey), y=correct spot (green)")

        while True:
            resp = input("server response (5 x ioy): ")
            resp = resp.replace(' ', '').strip()
            # print(f"{resp=}")

            if not all([
                len(resp) == 5,
                set(resp) & Wordle.response_set(), # intersection
            ]):
                print("invalid response, must be one of ioy 5 times")
                continue
            else:
                print()
                return resp

    def parse_response(self, guess, resp):
        def _elsewhere(p, c):
            """
            make a regex pattern
            .    -> [^c]
            [^c] -> [^cd]
            """
            if p == '.':
                return f"[^{c}]"

            chars = p[2:-1]
            return f"[^{chars}{c}]"

        contains = ''

        for i, l in enumerate(resp):
            c = guess[i]
            if l == Wordle.LETTER_IN:
                contains += c
                self.pattern[i] = _elsewhere(self.pattern[i], c)
            elif l == Wordle.LETTER_OUT:
                self.letter_counts[c] = 0
            elif l == Wordle.LETTER_EXACT:
                self.pattern[i] = c

        # excludes = [l for l, c in self.letter_counts.items() if c == 0]
        # print(f"{self.pattern}, {contains=}, {excludes=}")

        exact = ''.join(self.pattern)
        return exact, contains

    def make_guess(self):
        self.iteration += 1

        if self.length == 1:
            print(f"word must be: {self.words.pop()}")
            raise SystemExit

        if self.length == 0:
            print("our word list is now empty, we don't know the word")
            raise SystemExit

        print(f"current word list length: {self.length}")

        suggestions = self.get_suggestions()
        self.print_group(suggestions, 10)

        if self.first:
            raise SystemExit

        guess = self.get_guess()
        resp = self.get_response()
        exact, contains = self.parse_response(guess, resp)
        self.words = self.find_matches(exact, contains)

    def auto_solve(self):
        """
        given a word, show the steps the solver takes to find it
        """

        iteration = 0
        self.wordle = Wordle(args)
        self.wordle.word = args.word

        resp = None
        found_resp = Wordle.LETTER_EXACT * self.wordlen

        # doing this more complicated test instead of just self.length > 1
        # so that we show the last guess instead of breaking out of loop
        # one iteration too soon
        while (resp != found_resp) and (self.length > 0):
            iteration += 1
            curr_len = self.length
            suggestions = self.get_suggestions()
            guess = suggestions[0][0]
            resp = self.wordle.check_word(guess)
            exact, contains = self.parse_response(guess, resp)
            self.words = self.find_matches(exact, contains)

            print(f"round {iteration}: guess: {guess}, resp: {resp}, dict len: {curr_len}, {[v for v,c in suggestions[:5]]}")

        self.make_guess()

    def solve(self):

        # solve the provided word without interaction
        if args.word:
            self.auto_solve()
            return

        if args.count:
            self.print_letter_counts()
            return

        while True:
            self.make_guess()


def main(args):

    import_wordle()

    try:
        solver = Solver(args)
        solver.solve()
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='wordle solver')
    #parser.add_argument('--dict', default='/usr/share/dict/words', type=pathlib.Path)
    parser.add_argument('--dict', default='words5.txt', type=pathlib.Path)
    parser.add_argument('--len', default=5)
    parser.add_argument('--first', action='store_true', help="show first suggestion and exit")
    parser.add_argument('--count', action='store_true', help="show letter counts")
    parser.add_argument('word', nargs='?', help="automate solving of given word")
    args = parser.parse_args()

    main(args)
