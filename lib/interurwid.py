import pathlib
import itertools
import curses
import re
import asyncio
import string
import functools

import click

import urwid

import logging
logging.basicConfig(format="%(message)s", level=logging.INFO)
logging.getLogger('asyncio').setLevel(logging.WARNING)
logger = logging.getLogger()

from blinker import signal

class Signals:

    @staticmethod
    def urwid_to_blinker(signal, sender, value):
        """
        widget.connect(partial(urwid_to_blinker(blinker_signal)))
        """
        signal.send(sender, data=value)


    pattern_change  = signal('pattern_change', doc='called when word pattern updated')
    exclude_change  = signal('exclude_change', doc='called when exclude pattern updated')
    dict_loaded     = signal('dict_loaded', doc='called when dictionary loaded')
    wordlist_change = signal('wordlist_change', doc='called with updated word list')

signals = Signals()


from lib.wordle import Wordle


def get_input(win, pattern, excludes):

    win.clear()
    win.move(0, 0)
    win.addstr(f"pattern: {pattern}") # this updates cursor pos

    # y, x = win.getyx()
    # win.addstr(f"{y=} {x=}")

    c = win.getch() # retuns int, getkey returns str
    # win.addstr(f"{c=}")

    if chr(c) in 'abcdefghijklmnopqrstuvwxyz.':
        c = chr(c)
        pattern += c

        win_debug.clear()
        win_debug.refresh()
    elif c == ord('!'):
        c = win.getkey()
        excludes += c
    elif c in [127, curses.KEY_BACKSPACE]:
        pattern = pattern[0:-1]
    # elif c in [10, curses.KEY_ENTER]:
    #     # exit on enter if last character
    #     if len(pattern) == wordlen:
    #         raise KeyboardInterrupt
    elif c in [27]:                     # esc
        raise KeyboardInterrupt
    elif c in [3, 26]:                  # ctrl-c, ctrl-z
        raise KeyboardInterrupt
    else:
        win_debug.clear()
        win_debug.addstr(f"key code: {str(c)}")
        win_debug.refresh()

    win.refresh()

    return pattern, excludes

def update_excludes_win(win, excludes):
    win.clear()
    win.addstr(f"excludes (!c): {excludes}")
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
    win_counts = curses.newwin( 1, cols // 2, rows - 1, 0) # last row

    global win_debug
    win_debug = curses.newwin( 1, cols // 2, rows - 1, cols // 2) # last row

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



class Window(urwid.WidgetWrap):
    def __init__(self, *args, **kw):
        super().__init__(
            urwid.LineBox(*args, **kw)
        )

    def __repr__(self):
        return self.__class__.__name__

    @property
    def original_widget(self):
        return self._w

class WinPattern(Window):
    def __init__(self, *args, **kw):
        label = urwid.Text('pattern:')
        input = urwid.Padding(urwid.AttrMap(
            urwid.Edit('', '', multiline=False, *args, **kw),
            'default', 'editing'))
        widget = urwid.Columns([
                ("weight", 1, label),
                ("weight", 3, input),
            ], dividechars=-1)
        super().__init__(widget)

        self.prev = ''
        # urwid.connect_signal(self.edit_widget, "change", functools.partial(Signals.urwid_to_blinker, Signals.pattern_change))

    def keypress(self, size, key):

        if key == '!':
            self.prev = key
            return

        if self.prev == '!':
            signals.exclude_change.send('append', data=key)
            self.prev = ''
            return

        if key == 'backspace':
            self.text = self.text[:-1]
            return

        # handle the keypress if lowercase or .!
        if key not in string.ascii_lowercase + '.':
            return key

        # logger.debug(f"edit: {key}")

        self.text += key
        self.prev = key

    @property
    def edit_widget(self):
        return self.original_widget.original_widget.contents[1][0].original_widget.original_widget

    @property
    def text(self):
        return self.edit_widget.get_edit_text()

    @text.setter
    def text(self, text):
        self.edit_widget.set_edit_text(text)
        self.edit_widget.edit_pos = 100 # end

        signals.pattern_change.send('pattern', data=self.text)

class WinExcludes(Window):
    def __init__(self, *args, **kw):
        widget = urwid.Text('')
        super().__init__(widget, tlcorner='┬', blcorner='┴', )

        signals.exclude_change.connect(
            functools.partial(self.cb_exclude), weak=False
        )
        self.text = 'excludes: '

    def cb_exclude(self, sender, data):
        self.text = data

    @property
    def widget(self):
        return self.original_widget.original_widget

    @property
    def text(self):
        text, _ = self.widget.get_text()
        return text

    @text.setter
    def text(self, text):
        self.widget.set_text(self.text + text)

class WinMatches(Window):

    def __init__(self, *args, **kw):
        super().__init__(
            urwid.Filler(
                urwid.Text('matches'),
                valign='top',
            )
        )

        self.dictionary = []
        self.pattern = ''
        self.excludes = ''

        signals.dict_loaded.connect(
            functools.partial(self.cb_dict_loaded), weak=False
        )

        signals.pattern_change.connect(
            functools.partial(self.cb_pattern), weak=False
        )

        signals.exclude_change.connect(
            functools.partial(self.cb_exclude), weak=False
        )

    @property
    def widget(self):
        return self.original_widget.original_widget.original_widget

    @property
    def text(self):
        return self.widget.get_text()

    @text.setter
    def text(self, value):
        return self.widget.set_text(value)

    def cb_dict_loaded(self, sender, **kw):
        logger.info("loaded dictionary")
        self.dictionary = kw['data']

    def cb_pattern(self, sender, data):
        # logger.info(f"match pattern: {data}")
        self.pattern = data

    def cb_exclude(self, sender, data):
        self.excludes += data

    @property
    def dictionary(self):
        return self._dictionary

    @dictionary.setter
    def dictionary(self, value):
        logger.debug(f"dictionary={len(value)} words")
        self._dictionary = sorted(value)
        self.words = self.dictionary

    @property
    def words(self):
        return self._words

    @words.setter
    def words(self, value):
        self._words = value
        signals.wordlist_change.send('wordlist', data=self.words)

        if self.pattern:
            self.text = ' '.join(self.words)

    @property
    def pattern(self):
        try:
            return self._pattern
        except AttributeError:
            return ''

    @pattern.setter
    def pattern(self, value):
        logger.debug(f"pattern={value}")
        self._pattern = value
        self.recalc()

    @property
    def excludes(self):
        return self._excludes

    @excludes.setter
    def excludes(self, value):
        logger.debug(f"excludes={value}")
        self._excludes = value
        self.recalc()

    def recalc(self):
        logger.debug("recalculating wordlist")
        signals.wordlist_change.send('wordlist', data=self.words)

        if not self.pattern:
            self.text = ''
            self.words = self.dictionary
            return

        matches = self.pattern_match(self.words, self.pattern, self.excludes)
        self.words = matches

    def pattern_match(self, words, pattern, excludes):
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


class WinCounts(Window):
    def __init__(self, *args, **kw):
        font = urwid.Thin3x3Font()
        widget = urwid.Padding(
            urwid.BigText('', font),
            align='center', width='clip'
        )
        super().__init__(widget, title='Word Count', title_align='left')

        signals.wordlist_change.connect(functools.partial(self.cb_wordlist), weak=False)

    @property
    def widget(self):
        return self.original_widget.original_widget.original_widget

    def cb_wordlist(self, sender, data):
        self.widget.set_text(str(len(data)))

class WinLogging(Window):

    def __init__(self, *args, **kw):
        super().__init__(
            urwid.BoxAdapter(
                urwid.ListBox(urwid.SimpleListWalker([])),
                height=3
            ),
            title="Logging", title_align='left', tlcorner='┬', blcorner='┴',
        )

class MainFrame(urwid.Frame):
    def __init__(self, app, *args, **kw):
        super().__init__(urwid.Text(''), *args, **kw)

        self.app = app

        win_logging = WinLogging()
        win_count = WinCounts()
        win_pattern = WinPattern()
        win_excludes = WinExcludes()

        # win_global = urwid.LineBox(
        #     urwid.BoxAdapter(
        #         urwid.Filler( urwid.Text(''), valign='top'),
        #         height=3
        #     ),
        #     title="Global", title_align='left', tlcorner='┬', blcorner='┴',
        # )

        self.header = urwid.Columns([
            ("weight", 1, win_pattern),
            ("weight", 1, win_excludes),
        ],  dividechars=-1,)

        self.body = WinMatches()

        self.footer = urwid.Columns([
            ("weight", 1, win_count),
            ("weight", 2, win_logging),
        ], dividechars=-1)

        signals.pattern_change.connect(functools.partial(self.cb_signal_fired), weak=False)
        signals.exclude_change.connect(functools.partial(self.cb_signal_fired), weak=False)

    def cb_signal_fired(self, sender, **kw):
        # logger.debug(f"{sender=} value={kw['data']}")
        pass

    @property
    def win_logging(self):
        return self.footer.contents[1][0].original_widget.original_widget

    @property
    def win_plugin(self):
        return self.footer.contents[1][0].original_widget.original_widget.original_widget

    @property
    def body(self):
        return self._body

    @body.setter
    def body(self, widget):
        """
        widget should be a box or flow widget
        """
        super().set_body(widget)

class App:

    def __init__(self, args):
        self.args = args

    def setup(self):

        self.frame = MainFrame(self, focus_part='header')
        replace_handlers(logger, self.frame.win_logging)

        # self.frame.win_global.set_text("(Q)uit (N)ext (P)rev")

        # load and send dictionary to listeners
        wordle = Wordle(self.args['dict'], self.args['wordlen'])
        signals.dict_loaded.send(data=wordle.words)

    def run(self):
        palette = [
            # (name, foreground, background, mono, foreground_high, background_high)
            # standout is usually displayed with foreground and background reversed
            ('unfocused', 'default', '', '', '', ''),
            ('focused', 'light gray', 'dark blue', '', '#ffd', '#00a'),
            ('editing', 'black,underline', 'light gray', 'standout,underline', 'standout', 'black'),
            ('header', 'black,underline', 'light gray', 'standout,underline', 'white,underline,bold', 'black'),
            ('panel', 'light gray', 'dark blue', '', '#ffd', '#00a'),
            ('focus', 'light gray', 'dark cyan', 'standout', '#ff8', '#806'),
        ]

        event_loop = urwid.AsyncioEventLoop(loop=asyncio.get_event_loop())
        self.loop = urwid.MainLoop(self.frame,
                                   palette,
                                   unhandled_input=self.handle_keypress,
                                   handle_mouse=False,
                                   event_loop=event_loop,
                                   )

        self.loop.screen.set_terminal_properties(colors=256)
        self.loop.run() # blocking

    def handle_keypress(self, key):
        logger.debug(f"input: {key}")

        if type(key) is tuple and key and key[0].startswith('mouse'): # 'mouse press/release'
            logger.warn("no mouse support at this time")
            return

        # TODO get values from config
        if key in ('Q', 'f10', 'esc'):
            # FIXME why isn't self getting deleted?
            # if self.db:
            #     self.db.store()
            raise urwid.ExitMainLoop()

        # hotkey to direct select of plugin
        if key in string.ascii_uppercase:
            plugin = self.find_plugin(key)

            if plugin is not None:
                self.plugin = plugin
                return

        # it's ' ' not 'space'

        if key == 'N':
            self.next_plugin()
        elif key == 'P':
            self.prev_plugin()

        return key


class UrwidHandler(logging.StreamHandler):
    def __init__(self, listbox):
        super().__init__()
        self.queue = [] # collections.deque(maxlen=5) # TODO make MonitoredList a MonitoredQueue
        self.listbox = listbox

    def emit(self, record):
        msg = self.format(record)
        msg = urwid.Text(msg)
        self.listbox.body.append(msg)
        self.listbox.set_focus(len(self.listbox.body) - 1) # scroll to last line

def replace_handlers(logger, listbox):
    """
    replace current handlers and emit to given urwid.ListBox
    """
    logger.handlers = [UrwidHandler(listbox)]

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

    app = App(args)
    app.setup()
    app.run()       # blocking call
