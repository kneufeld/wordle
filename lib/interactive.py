#!/usr/bin/env python

import pathlib
import itertools
import curses
import re

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

def show_matches(win, pattern, matches):
    win.clear()
    win.move(0, 0)
    rows, cols = win.getmaxyx()

    if not pattern:
        win.refresh()
        return

    for match in matches:
    # for match in matches[:20]:
        row, col = win.getyx()
        # win.addstr(0, 0, f"{rows=} {cols=} {row=} {col=}")

        if row == (rows - 1) and ((col + len(match) + 2) >= cols):
            break

        win.addstr(match + ' ')
        # try:
        #     win.addstr(match + ' ')
        # except curses.error:
        #     break

    win.refresh()

def get_input(win, pattern, excludes):

    win.clear()
    win.move(0, 0)
    win.addstr(f"pattern: {pattern}") # this updates cursor pos

    # y, x = win.getyx()
    # win.addstr(f"{y=} {x=}")

    c = win.getch() # retuns int, getkey returns str
    # win.addstr(f"{c=}")

    if c in list(range(ord('a'), ord('z'))) + [ord('.')]:
        c = chr(c)
        pattern += c
    elif c == ord('!'):
        c = win.getkey()
        excludes += c
    elif c in [127, curses.KEY_BACKSPACE]:
        pattern = pattern[0:-1]
    elif c in [10, curses.KEY_ENTER]:
        # exit on enter if last character
        if len(pattern) == wordlen:
            raise KeyboardInterrupt
    elif c in [3, 26]:                  # ctrl-c, ctrl-z
        win.addstr('ctrl-c')
        raise KeyboardInterrupt
    else:
        win.addstr(str(c))

    win.refresh()

    return pattern, excludes

def pattern_match(words, pattern, excludes):
    if not pattern:
        pattern = '.' * wordlen

    matches = []
    pattern = re.compile(pattern)

    for word in words:
        if all([
            pattern.match(word),     # re.match is beginning of string
            not any([c in word for c in excludes]),
        ]):
            matches.append(word)

    return sorted(matches)

def update_excludes_win(win, excludes):
    win.clear()
    win.addstr(f"excludes: {excludes}")
    win.refresh()

def update_count_win(win, words):
    win.clear()
    win.addstr(f"word count: {len(words)}")
    win.refresh()

def interactive(stdscr, args):

    wordle = Wordle(args['dict'], args['wordlen'])
    dictionary = wordle.words

    # curses.echo()
    stdscr.clear()
    stdscr.refresh()

    rows, cols = stdscr.getmaxyx()
    win_pattern = curses.newwin(1, cols // 2, 0, 0)
    win_excludes = curses.newwin(1, cols // 2, 0, cols // 2)
    win_matches = curses.newwin(rows - 4, cols, 2, 0)
    win_counts = curses.newwin( 1, cols, rows - 1, 0) # last row

    try:
        excludes = args['excludes']
        pattern = ''
        matches = pattern_match(dictionary, pattern, excludes)

        update_count_win(win_counts, matches)
        update_excludes_win(win_excludes, excludes)

        while True:
            pattern, excludes = get_input(win_pattern, pattern, excludes)
            matches = pattern_match(dictionary, pattern, excludes)
            update_excludes_win(win_excludes, excludes)
            update_count_win(win_counts, matches)
            show_matches(win_matches, pattern, matches)

    except KeyboardInterrupt:
        pass

    # stdscr.getkey()

@click.command()
@click.option('--dict', default='dictionary.txt', type=click.Path(exists=True, readable=True, path_type=pathlib.Path))
@click.option('--len', 'wordlen', default=5, type=int)
@click.option('--exclude', '-e', 'excludes', metavar='letters', default='', type=str)
@click.pass_context
def cli(ctx, *_, **args):
    """
    interactively solve a Wordle puzzle by showing updated word list based on given pattern

    \b
    .  for wildcard
    !c to add a letter to the exclude list
    """

    global wordlen
    wordlen = args['wordlen']

    try:
        curses.wrapper(interactive, args)
    except KeyboardInterrupt:
        pass
