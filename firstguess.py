#!/usr/bin/env python

"""
given all the words, select a good first guess based on letter distribution
"""

import random
import collections
import itertools

import lib
wordlen = lib.wordlen

import logging
logging.basicConfig(format='%(message)s', level=logging.DEBUG)
logger = logging.getLogger()

def pretty_print(d, n=10):
    if not n:
        n = len(d)

    if not isinstance(d, dict):
        d = dict(d)

    for i, (k, v) in enumerate(d.items()):
        if i != (n-1):
            print(f"{k}: {v}", end=', ')
        else:
            print(f"{k}: {v}")
            break

def group_print(d, n=10):
    if not n:
        n = len(d)

    if isinstance(d, dict):
        d = list(d.items())

    # for i in range(n):
    #     print(d[0][1], end=': ')

    for i, (k, v) in enumerate(itertools.groupby(d, key=lambda item: item[1])):
        if i >= (n-1):
            break

        print(f"{k}: {', '.join([k for k,v in v])}")

def count_letters(words):
    """
    count number of times each letter occurs in all words
    """
    counts = collections.defaultdict(int)

    for word in words:
        for letter in word:
            counts[letter] += 1

    return counts

def word_score(counts, word):
    score = 0

    for l in word:
        score += counts[l]

    return score

def sub_analyze(words, counts):
    sorted_letters = sorted(counts.items(), key=lambda item: item[1], reverse=True)
    common_letters = [l for l, c in sorted_letters[:3]]
    guesses = lib.find_matches(words, ',' + ''.join(common_letters))

    print("\nhighest scoring words")
    scored = dict([(word, word_score(counts, word)) for word in guesses])
    top = sorted(scored.items(), key=lambda item: item[1], reverse=True)
    return top

def analyze(words):

    # show the most common letters
    counts = count_letters(words)
    sorted_letters = sorted(counts.items(), key=lambda item: item[1], reverse=True)
    pretty_print(sorted_letters, 0)

    top = sub_analyze(words, counts)
    group_print(top, 10)
    print(f"earth: {word_score(counts, 'earth')}")

    print("\nhighest scoring words without vowels")

    for vowel in "aeiou":
        counts[vowel] = 0

    top = sub_analyze(words, counts)
    group_print(top, 10)
    print(f"earth: {word_score(counts, 'earth')}")

def main():

    words = lib.read_dict(lib.dictfile, wordlen)
    analyze(words)

if __name__ == '__main__':

    main()
