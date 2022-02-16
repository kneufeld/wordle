import pathlib
import random

import click

from .wordle import Wordle
from .utils import dotdict

from rich.console import Console
_print = print
print = Console(color_system='truecolor', highlight=False).print


class WordleUI:

    # KN: all this might be a little too DRY...

    EMOJI_IN     = '🟨'
    EMOJI_OUT    = '⬜'
    EMOJI_EXACT  = '🟩'

    @classmethod
    def colorize(cls, code, text):
        """
        colorize text using rich color tags
        code: a Wordle.LETTER_X response
        text: the text to wrap with color tags
        """
        if code == Wordle.LETTER_IN:
            color = 'bold dark_goldenrod'
        elif code == Wordle.LETTER_OUT:
            color = 'grey'
        elif code == Wordle.LETTER_EXACT:
            color = 'green'
        else:
            raise RuntimeError(f"unknown code: {code}")

        return f"[{color}]{text}[/{color}]"

    @classmethod
    def colorize_word(cls, resp, word):
        return ''.join([
            cls.colorize(r, w)
            for r, w in zip(resp, word)
        ])

    def __init__(self, args):
        args = dotdict(args)

        self.args   = args
        self.wordle = Wordle(args.dict, args.wordlen)
        self.rounds = [] # [guess, response]

    @property
    def wordlen(self):
        return self.args.wordlen

    def get_guess(self):
        def validate_guess(word):
            if len(word) != self.wordlen:
                return "wrong word length"

            if word not in self.wordle.words:
                return "your guess is not in dictionary"

            return None

        while True:
            word = input("what's your guess: ")
            word = word.lower()

            if reason := validate_guess(word):
                print(f"invalid guess: {reason}")
                continue

            return word

    def print_response(self, resp):
        for c in resp:
            print(WordleUI.colorize(c, '◼'), end=' ')
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

    def pick_word(self, words):
        # can't random.choice from a set so use this hack
        return random.sample(words, 1)[0]

    def play(self):

        if self.args.start_word:
            self.word = self.args.start_word
            print(f"using given word: {self.args.start_word}")
        else:
            self.word = self.pick_word(self.wordle.words)
            print("I picked a word, what's your guess?")

        for i in range(6):
            guess = self.get_guess()
            resp = self.wordle.check_word(self.word, guess)

            self.rounds.append([guess, resp])
            self.show_rounds()

            if resp == Wordle.LETTER_EXACT * self.wordlen:
                print(f"[bold green]You got it in {len(self.rounds)} tries![/bold green]")
                self.show_summary()
                return

        print(f"[bold yellow]You ran out of tries. The word was: [blue]{self.wordle.word}[/blue][/bold yellow]")
        self.show_summary()

@click.command()
@click.option('--dict', default='words5.txt', type=click.Path(exists=True, readable=True, path_type=pathlib.Path))
@click.option('--len', 'wordlen', default=5)
@click.argument('start_word', required=False) # text="use this word instead of a random one")
@click.pass_context
def cli(ctx, *args, **kw):
    """
    play a game of wordle

    provide a START_WORD to force a specific one (useful for testing) or
    omit and a random word from the dictionary file will be chosen.
    """
    # import pudb; pu.db

    try:
        ui = WordleUI(kw)
        ui.play()
    except KeyboardInterrupt:
        pass
