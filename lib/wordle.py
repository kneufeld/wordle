
class Wordle:

    LETTER_IN    = 'i' # in, in word but wrong spot
    LETTER_OUT   = 'o' # out, not in word
    LETTER_EXACT = 'e' # exact spot

    def __init__(self, dictpath, wordlen):
        self.words = self.read_dict(dictpath, wordlen)

    @property
    def words(self):
        """
        current subset of dictionary words that could be solution
        """
        return self._words

    @words.setter
    def words(self, words):
        self._words = words

    @property
    def length(self):
        return len(self.words)

    @classmethod
    def response_set(cls):
        return set([
            cls.LETTER_IN,
            cls.LETTER_OUT,
            cls.LETTER_EXACT,
        ])

    @classmethod
    def read_dict(cls, dictpath, wordlen):
        dictionary = dictpath.open().read().splitlines()
        print(f"starting dictionary contains {len(dictionary)} words")

        words = set()

        for word in dictionary:
            if all([
                len(word) == wordlen,       # 5 letters long
                # turns out you can have repeat letters
                # len(set(word)) == wordlen,  # 5 unique letters, not the same as above, eg. otter
                word == word.lower()        # no capitals
            ]):
                words.add(word)

        # logger.debug(f"our word list contains {len(words)}, {wordlen} letter words")
        assert words, f"our dictionary is empty after reading file: {dictpath}"
        return words

    def check_word(self, word, guess):
        """
        return a response for the given guess
        """

        resp = ''

        for i in range(len(word)):
            if guess[i] == word[i]:
                resp += self.LETTER_EXACT
            elif guess[i] in word:
                resp += self.LETTER_IN
            else:
                resp += self.LETTER_OUT

        return resp
