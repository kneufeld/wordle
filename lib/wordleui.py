import pathlib
import random

import click

from rich.console import Console
_print = print
print = Console(color_system='truecolor', highlight=False).print


from .wordle import Wordle


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

            if resp == Wordle.LETTER_EXACT * self.wordle.wordlen:
                print(f"[bold green]You got it in {len(self.rounds)} tries![/bold green]")
                self.show_summary()
                return

        print(f"[bold yellow]You ran out of tries. The word was: [blue]{self.wordle.word}[/blue][/bold yellow]")
        self.show_summary()

@click.command()
@click.option('--dict', default='words5.txt', type=click.Path(exists=True, readable=True, path_type=pathlib.Path))
@click.option('--len', 'wordlen', default=5)
@click.argument('start_word', required=False) #, text="use this word instead of a random one")
@click.pass_context
def cli(ctx, *args, **kw):
    # import pudb; pu.db

    try:
        wordle = Wordle(kw)
        ui = WordleUI(wordle)
        ui.play()
    except KeyboardInterrupt:
        pass
