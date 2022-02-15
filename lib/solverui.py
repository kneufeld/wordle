import pathlib
import argparse
import re
import collections
import itertools

import click

from rich.console import Console
_print = print
print = Console(color_system='truecolor', highlight=False).print

from lib.wordle import Wordle
from lib.utils import dotdict, colorize
from lib.solver import Solver

def to_list(ctx, param, value):
    return list(value)

class SolverUI:

    def __init__(self, args):
        args = dotdict(args)
        self.args = args

        self.solver = Solver(args)
        self.wordlen = args.wordlen
        self.iteration = 0     # what attempt are we on
        self.pattern = ['.'] * self.wordlen

    def print_group(self, words, n=10):
        if not n:
            n = len(words)

        if isinstance(words, dict):
            words = list(words.items())

        for i, (k, v) in enumerate(itertools.groupby(words, key=lambda item: item[1])):
            if i >= n:
                break

            print(f"{int(k)}: {', '.join([k for k, _ in v])}")

    def print_letter_counts(self):
        by_letter = sorted(self.solver._letter_counts.items())

        print("\nin alphabetical order:\n", end='')
        for l, c in by_letter:
            print(f"{l}: {c}", end=', ')
        print()

        # in count order
        by_count = sorted(self.solver._letter_counts.items(), key=lambda item: item[1], reverse=True)

        print("\nin numerical order:\n", end='')
        for l, c in by_count:
            print(f"{l}: {c}", end=', ')
        print()

    def get_guess(self):
        def validate_guess(word):
            return len(word) == self.wordlen

        while True:
            word = input("what's your guess: ")
            word = word.lower()

            if not validate_guess(word):
                print("invalid guess, try again")
                continue

            return word

    def get_response(self):
        """
        ask user to type in response from wordle
        """
        print("i=letter in word (yellow), o=letter not in word (grey), e=exact spot (green)")

        while True:
            resp = input("server response (5 x ioe): ")
            resp = resp.replace(' ', '').strip()
            # print(f"{resp=}")

            if not all([
                len(resp) == 5,
                set(resp) <= Wordle.response_set(), # resp is subset of response set
            ]):
                print("invalid response, must be one of ioe 5 times")
                continue
            else:
                print()
                return resp

    def cb_iteration(self, *args, **kw):
        iteration   = kw['iteration']
        words       = kw['words']
        curr_len    = kw['curr_len']
        suggestions = kw['suggestions']
        guess       = kw['guess']
        resp        = kw['resp']

        guess = colorize(guess, resp)
        print(f"round {iteration}: guess: {guess}, resp: {resp}, dict len: {curr_len}, {[v for v,c in suggestions[:5]]}")

        if len(suggestions) == 1:
            print(f"word is: {words.pop()}")
        elif len(suggestions) == 0:
            print("our word list is now empty, we don't know the word")


    def make_guess(self):
        self.iteration += 1
        length = self.solver.length

        if length == 1:
            print(f"word must be: {self.solver.words.pop()}")
            raise SystemExit

        if length == 0:
            print("our word list is now empty, we don't know the word")
            raise SystemExit

        print(f"current word list length: {length}")

        suggestions = self.solver.get_suggestions()
        self.print_group(suggestions, 10)

        if self.args.first:
            raise SystemExit

        guess = self.get_guess()
        resp = self.get_response()
        self.solver.make_guess(guess, resp)

    def solve(self):

        # solve the provided word without interaction
        if self.args.word:
            word = self.args.word.pop(0)
            self.solver.auto_solve(word, self.args.word, self.cb_iteration)
            return

        if self.args.score:
            word = self.args.score
            word_score = int(self.solver.word_score(word))
            print(f"{word}: {word_score}")
            return

        if self.args.count:
            self.print_letter_counts()
            return

        while True:
            self.make_guess()


@click.command()
@click.option('--dict', default='words5.txt', type=pathlib.Path)
@click.option('--len', 'wordlen', default=5, type=int)
@click.option('--first', is_flag=True, help="show first suggestion and exit")
@click.option('--count', is_flag=True, help="show letter counts")
@click.option('--score', metavar='word', help="show word score")
@click.argument('word', required=False, nargs=-1, callback=to_list) # help="automate solving of given word")
@click.pass_context
def cli(ctx, *_, **args):

    try:
        solver = SolverUI(args)
        solver.solve()
    except KeyboardInterrupt:
        pass
