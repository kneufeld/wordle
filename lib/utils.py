def splice(s, i, c):
    """
    replace letter in string at position i
    aka: s[i] = c
    """
    return s[:i] + c + s[i + 1:]

class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = lambda self, key: self[key]
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

# from https://stackoverflow.com/questions/128573/using-property-on-classmethods/64738850#64738850
# Python 3.9 allows @classmethod then @property on a method
class classproperty(object):

    def __init__(self, fget):
        self.fget = fget

    def __get__(self, owner_self, owner_cls):
        return self.fget(owner_cls)
