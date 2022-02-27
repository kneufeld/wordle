import pathlib
import curses
import re
import asyncio
import string
import functools

import click
import urwid
from blinker import signal

import logging
logging.basicConfig(format="%(message)s", level=logging.INFO)
logging.getLogger('asyncio').setLevel(logging.WARNING)
logger = logging.getLogger()

from lib.wordle import Wordle

class Signals:

    @staticmethod
    def urwid_to_blinker(signal):
        """
        usage: widget.connect(urwid_to_blinker(blinker_signal))
        blinker handler must accept 'data' as keyword
        """
        def _converter(sender, data):
            return signal.send(sender, data=data)
        return _converter


    pattern_change  = signal('pattern_change', doc='called when word pattern updated')
    exclude_change  = signal('exclude_change', doc='called when exclude pattern updated')
    dict_loaded     = signal('dict_loaded', doc='called when dictionary loaded')
    wordlist_change = signal('wordlist_change', doc='called with updated word list')

signals = Signals()



class Window(urwid.WidgetWrap):
    def __init__(self, *args, **kw):
        super().__init__(
            urwid.LineBox(*args, **kw)
        )

    def __repr__(self):
        return self.__class__.__name__

    @property
    def original_widget(self):
        # return what's inside the LineBox
        return self._w


class WinPattern(Window):
    def __init__(self, *args, **kw):
        label = urwid.Text('pattern:')
        input = urwid.AttrMap(
            urwid.Edit('', '', multiline=False, align='left', wrap='clip',),
            'default', 'focused')
        widget = urwid.Columns([
                (10, label),
                (6, input),
                ('weight', 2, urwid.Padding(urwid.Text(''))),
        ], dividechars=-1)

        super().__init__(widget)

        self.prev = ''
        # urwid.connect_signal(self.widget, "change", Signals.urwid_to_blinker(Signals.pattern_change))

    def keypress(self, size, key):

        if key == '!':
            self.prev = key
            return

        if self.prev == '!':
            signals.exclude_change.send('exclude', data=key)
            self.prev = ''
            return

        if key == 'backspace':
            self.text = self.text[:-1]
            return

        # propagate keypress if not a letter or .
        if key not in string.ascii_lowercase + '.':
            return key

        # logger.debug(f"edit: {key}")

        # only allow 5 chars
        if len(self.text) >= app.args['wordlen']:
            return

        self.text += key
        self.prev = key

    @property
    def widget(self):
        return self.original_widget.original_widget.contents[1][0].original_widget

    @property
    def text(self):
        return self.widget.get_edit_text()

    @text.setter
    def text(self, text):
        self.widget.set_edit_text(text)
        self.widget.edit_pos = 100 # end

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
                urwid.Text('. is a wildcard\n! to exclude a letter'),
                valign='top',
            )
        )

        self._pattern = ''
        self._excludes = ''

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

    def cb_dict_loaded(self, sender, data):
        logger.info("loaded dictionary")
        self.dictionary = data

    def cb_pattern(self, sender, data):
        # logger.info(f"match pattern: {data}")
        self.pattern = data

    def cb_exclude(self, sender, data):
        self.excludes += data
        self.dictionary = self.pattern_match(self.dictionary, '.' * app.args['wordlen'], self.excludes)

    @property
    def dictionary(self):
        return self._dictionary

    @dictionary.setter
    def dictionary(self, value):
        logger.debug(f"dictionary has {len(value)} words")
        self._dictionary = sorted(value)

    @property
    def words(self):
        return self._words

    @words.setter
    def words(self, value):
        self._words = value
        signals.wordlist_change.send('wordlist', data=self.words)

        if app.args['invisible']:
            self.text = 'running in invisible mode'
        elif self.pattern:
            self.text = ' '.join(self.words)
        else:
            self.text = ''

    @property
    def pattern(self):
        return self._pattern

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

        if self.pattern:
            self.words = self.pattern_match(self.dictionary, self.pattern, self.excludes)
        else:
            self.words = self.dictionary

    def pattern_match(self, words, pattern, excludes):
        if not pattern:
            pattern = '.' * app.args['wordlen']

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

        signals.dict_loaded.connect(functools.partial(self.cb_wordlist), weak=False)
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

        # load and send dictionary to listeners
        wordle = Wordle(self.args['dict'], self.args['wordlen'])
        signals.dict_loaded.send(data=wordle.words)

    def run(self):
        palette = [
            # (name, foreground, background, mono, foreground_high, background_high)
            # standout is usually displayed with foreground and background reversed
            ('unfocused', 'default', '', '', '', ''),
            ('focused', 'light gray', 'dark blue', '', '#ffd', '#00a'),
            ('editing', 'dark blue', 'light gray', '', 'standout', 'black'),
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
@click.option('--invisible', '-i', is_flag=True, help="don't show matching words, just count")
@click.pass_context
def cli(ctx, *_, **args):
    """
    interactively solve a Wordle puzzle by showing updated word list based on given pattern

    \b
    .  for wildcard
    !c to add a letter to the exclude list
    """

    global app
    app = App(args)
    app.setup()

    for e in args['excludes']:
        signals.exclude_change.send('exclude', data=e)

    app.run()       # blocking call
