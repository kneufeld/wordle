def splice(s, i, c):
    """
    replace letter in string at position i
    aka: s[i] = c
    """
    return s[:i] + c + s[i + 1:]

class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

def colorize(guess, resp):
    """
    return a rich compatible string of the guess
    """
    from .wordle import Wordle

    resp = list(resp)
    for i, c in enumerate(resp):
        g = guess[i]
        if c == Wordle.LETTER_IN:
            resp[i] = f"[bold dark_goldenrod]{g}[/bold dark_goldenrod]"
        elif c == Wordle.LETTER_OUT:
            resp[i] = f"[grey]{g}[/grey]"
        elif c == Wordle.LETTER_EXACT:
            resp[i] = f"[green]{g}[/green]"

    # print(f"{resp=}", highlight=False, markup=False)
    return ''.join(resp)
