import pathlib
import itertools
import copy

import click

from rich.console import Console
_print = print
print = Console(color_system='truecolor', highlight=False).print

from lib.wordle import Wordle
from lib.wordleui import WordleUI
from lib.utils import dotdict
from lib.solver import Solver

def to_list(ctx, param, value):
    return list(value)

class ReverserUI:

    def __init__(self, args):
        args = dotdict(args)

        self.args = args
        self.word = args.word
        self.solver  = Solver(args)
        self.summary = self.parse_summary(args.summary)

    @property
    def wordle(self):
        return self.solver.wordle

    @property
    def words(self):
        """
        current subset of dictionary words that have could be solution
        """
        return self.wordle.words

    @words.setter
    def words(self, words):
        self.wordle.words = words

    @property
    def length(self):
        return len(self.words)

    def parse_summary(self, spath):
        """
        convert the emoji summary and convert to text
        reverse the order so the answer is first
        """

        summary = spath.open().read().splitlines()
        ret = []

        for line in summary:
            _line = []
            for r in line:
                if r in WordleUI.EMOJI_IN:
                    _line.append(Wordle.LETTER_IN)
                elif r in WordleUI.EMOJI_OUT:
                    _line.append(Wordle.LETTER_OUT)
                elif r in WordleUI.EMOJI_EXACT:
                    _line.append(Wordle.LETTER_EXACT)
            ret.append(_line)

        ret.reverse()
        # print(summary)
        # print(ret)
        return ret

    def parse_resp(self, resp):
        """
        covert response to [exact, contains, excludes] tuple that
        we can use to filter words
        """
        pass

    def filter_words(self, word, resp):
        """
        given a word and the response, return a list of words
        that match that pattern

        Note: resp is the previous response to the given words
        """
        words = copy.copy(self.words)



@click.command()
@click.option('--dict', default='dictionary.txt', type=click.Path(exists=True, readable=True, path_type=pathlib.Path))
@click.option('-s', '--summary', default='summary.txt', required=True, type=click.Path(exists=True, readable=True, path_type=pathlib.Path))
@click.argument('word', required=True, nargs=1)
@click.argument('guesses', required=False, nargs=-1, callback=to_list)
@click.pass_context
def cli(ctx, *_, **args):
    """
    try to reverse a Wordle puzzle given the word and summary.

    This is probably computationally impossible.
    """

    try:
        app = ReverserUI(args)
        # app.run()
    except KeyboardInterrupt:
        pass
