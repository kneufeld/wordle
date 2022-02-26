import re
import collections

from lib.wordle import Wordle
from lib.utils import splice, dotdict

class Solver:

    def __init__(self, args):
        args = dotdict(args)

        self.wordlen   = args.wordlen
        self.wordle    = Wordle(args.dict, args.wordlen)
        self.iteration = 0     # what attempt are we on
        self.pattern   = ['.'] * self.wordlen

        self.update_letter_stats()

    @property
    def words(self):
        """
        current subset of dictionary words that have could be solution
        """
        return self.wordle.words

    @words.setter
    def words(self, words):
        self.wordle.words = words
        self.update_letter_stats()

    @property
    def length(self):
        return len(self.words)

    def update_letter_stats(self):
        if not self.words:
            return

        self._letter_counts = self.letter_counts(self.words)
        self._letter_dist = self.letter_distribution(self.words)

    def letter_counts(self, words):
        """
        count number of times each letter occurs in all words
        """
        counts = collections.defaultdict(int)

        for word in words:
            for c in word:
                counts[c] += 1

        return counts

    def letter_distribution(self, words):
        """
        return a dict with letter percentages of each location
        dist['a'][0] = .02 # 2% of words start with 'a'
        dist['a'][4] = .02 # 2% of words end with 'a'
        """
        def count_matches(words, pattern):
            return sum([
                1 for word in words if pattern.match(word)
            ])

        dist = collections.defaultdict(lambda: [0] * self.wordlen)

        for c in range(26):
            c = chr(ord('a') + c)

            for i in range(self.wordlen):
                pattern = '.' * self.wordlen
                pattern = splice(pattern, i, c)
                pattern = re.compile(pattern)
                matches = count_matches(self.words, pattern)

                dist[c][i] = matches / len(words)

        return dist

    def word_score(self, word):
        score = sum([
            self._letter_counts[c] for c in set(word)
        ])
        # return score

        # how often is the letter in that position in the word
        per = sum([self._letter_dist[c][i] for i, c in enumerate(word)])
        per /= self.wordlen # average letter position
        score *= 1 + per

        return score

    def find_matches(self, exact, contains, excludes):
        """
        "exact" is a bit of a misnomer, it's anything or exact
        """
        matches = set()
        exact = re.compile(exact)

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

        # NOTE: the sorted function below warrants an explanation. It turns out
        # this solver was non deterministic because the word list is a set so
        # after sorting by score sometimes two words with same score would be
        # swapped. By sorting on (score, word) (ie: a two pass sort but in one
        # pass) the suggestion list is now stable so this is now deterministic.
        # Also, by negating (-item) and sorting by reverse=False it's the equiv
        # of rerverse=True but the actual words are then sorted in alphabetical
        # order.

        suggestions = [(word, self.word_score(word)) for word in self.words]
        suggestions = sorted(suggestions, key=lambda item: (-item[1], item[0]), reverse=False)

        return suggestions

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
        excludes = ''

        for i, r in enumerate(resp):
            c = guess[i]
            if r == Wordle.LETTER_IN:
                contains += c
                self.pattern[i] = _elsewhere(self.pattern[i], c)
            elif r == Wordle.LETTER_OUT:
                excludes += c
            elif r == Wordle.LETTER_EXACT:
                self.pattern[i] = c

        exact = ''.join(self.pattern)
        return exact, contains, excludes

    def prune_words(self, guess, resp):
        """
        given a guess and a wordle response, prune our current
        word list to exclude impossible answers
        """
        exact, contains, excludes = self.parse_response(guess, resp)
        self.words = self.find_matches(exact, contains, excludes)

    def solve(self, word, guesses=None, callback=None):
        """
        given a word, show the steps the solver takes to find it
        """
        self.iteration = 0

        while self.length >= 1:
            self.iteration += 1
            curr_len        = self.length
            suggestions     = self.get_suggestions()

            if guesses:
                guess = guesses.pop(0)
            else:
                guess = suggestions[0][0]

            resp = self.wordle.check_word(word, guess)
            self.prune_words(guess, resp)

            if callback:
                callback(
                    iteration=self.iteration,
                    words=self.words,
                    curr_len=curr_len,
                    suggestions=suggestions,
                    guess=guess,
                    resp=resp
                )
