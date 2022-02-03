#!/usr/bin/env python

import pathlib
import argparse
import re
import collections
import itertools
import readline

class Solver:

    def __init__(self, dpath, wordlen=5):
        self.wordlen = wordlen
        self.words = self.read_dict(dpath, self.wordlen)
        self.letter_counts = self.count_letters(self.words)
        self.iteration = 0     # what attempt are we on
        self.pattern = ['.'] * wordlen

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

    def count_letters(self, words):
        """
        count number of times each letter occurs in all words
        """
        counts = collections.defaultdict(int)

        for word in words:
            for letter in word:
                counts[letter] += 1

        return counts

    def word_score(self, word):
        return sum([
            self.letter_counts[c] for c in word
        ])

    def find_matches(self, exact, contains):
        """
        "exact" is a bit of a misnomer, it's anything or exact
        """
        matches = set()
        exact = re.compile(exact)
        exclude = [c for c, v in self.letter_counts.items() if v == 0]

        for word in self.words:
            if all([
                exact.match(word),
                all([l in word for l in contains]),
                not any([l in word for l in exclude])
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

    def group_print(self, words, n=10):
        if not n:
            n = len(words)

        if isinstance(words, dict):
            words = list(words.items())

        for i, (k, v) in enumerate(itertools.groupby(words, key=lambda item: item[1])):
            if i >= n:
                break

            print(f"{k}: {', '.join([k for k, _ in v])}")

    def get_guess(self):

        while True:
            word = input("what's your guess: ")
            word = word.lower()

            if not self.validate_guess(word):
                print("invalid guess, try again")
                continue

            return word

    def get_response(self):
        print("i=letter in word (yellow), o=letter not in word (grey), y=correct spot (green)")

        while True:
            resp = input("server response (5 x ioy): ")
            resp = resp.replace(' ', '').strip()
            # print(f"{resp=}")

            if not all([
                len(resp) == 5,
                set(resp) & set('ioy'), # intersection
            ]):
                print("invalid response, must be one of ioy 5 times")
                continue
            else:
                print()
                return resp

    def parse_response(self, guess, resp):
        def _elsewhere(p, c):
            if p == '.':
                return f"[^{c}]"

            chars = p[2:-1]
            return f"[^{chars}{c}]"

        def splice(s, i, c):
            return s[:i] + c + s[i + 1:]

        contains = ''

        for i, l in enumerate(resp):
            c = guess[i]
            if l == 'i':
                contains += c
                self.pattern[i] = _elsewhere(self.pattern[i], c)
            elif l == 'o':
                self.letter_counts[c] = 0
            elif l == 'y':
                self.pattern[i] = c

        # print(self.pattern, contains)

        exact = ''.join(self.pattern)
        return exact, contains

    def make_guess(self):
        self.iteration += 1

        if self.length == 1:
            print(f"word must be: {self.words.pop()}")
            raise KeyboardInterrupt

        if self.length == 0:
            print("our word list is now empty, we don't know the word")
            raise KeyboardInterrupt

        print(f"current word list length: {self.length}")

        suggestions = self.get_suggestions()
        self.group_print(suggestions, 10)

        guess = self.get_guess()
        resp = self.get_response()
        exact, contains = self.parse_response(guess, resp)
        self.words = self.find_matches(exact, contains)

    def solve(self):
        # while self.iteration < 6:
        while True:
            self.make_guess()

def main(args):

    solver = Solver(args.dict, args.len)

    try:
        solver.solve()
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='wordle solver')
    #parser.add_argument('--dict', default='/usr/share/dict/words', type=pathlib.Path)
    parser.add_argument('--dict', default='words5.txt', type=pathlib.Path)
    parser.add_argument('--len', default=5)
    args = parser.parse_args()

    main(args)
