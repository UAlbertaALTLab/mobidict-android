import sqlite3
import os

from typing import Dict, Iterable, List, NewType, Tuple
from collections import defaultdict
import dawg
from itertools import chain

import unicodedata
from unicodedata import normalize
from core.SearchRun import SearchRun
from core.typesCore import Result


SimplifiedForm = NewType("SimplifiedForm", str)


def _reverse(text: SimplifiedForm) -> SimplifiedForm:
    return SimplifiedForm(text[::-1])


class AffixSearcher:
    """
    Enables prefix and suffix searches given a list of words and their wordform IDs.
    """

    def __init__(self, words: Iterable[Tuple[str, int]]):
        self.text_to_ids: Dict[str, List[int]] = defaultdict(list)

        words_marked_for_indexing = [
            (simplified_text, wordform_id)
            for raw_text, wordform_id in words
            if (simplified_text := self.to_simplified_form(raw_text))
        ]

        for text, wordform_id in words_marked_for_indexing:
            self.text_to_ids[self.to_simplified_form(text)].append(wordform_id)

        if True:
            self._prefixes = dawg.CompletionDAWG(
                [text for text, _ in words_marked_for_indexing]
            )
            self._suffixes = dawg.CompletionDAWG(
                [_reverse(text) for text, _ in words_marked_for_indexing]
            )

    def search_by_prefix(self, prefix: str) -> Iterable[int]:
        """
        :return: an iterable of Wordform IDs that match the prefix
        """
        term = self.to_simplified_form(prefix)
        matched_words = self._prefixes.keys(term)
        return chain.from_iterable(self.text_to_ids[t] for t in matched_words)

    def search_by_suffix(self, suffix: str) -> Iterable[int]:
        """
        :return: an iterable of Wordform IDs that match the suffix
        """
        term = self.to_simplified_form(suffix)
        matched_reversed_words = self._suffixes.keys(_reverse(term))
        return chain.from_iterable(
            self.text_to_ids[_reverse(t)] for t in matched_reversed_words
        )

    @staticmethod
    def to_simplified_form(query: str) -> SimplifiedForm:
        """
        Convert to a simplified form of the word and its orthography to facilitate affix
        search.  You SHOULD throw out diacritics, choose a Unicode Normalization form,
        and choose a single letter case here!
        """
        return SimplifiedForm(to_source_language_keyword(query.lower()))


# def do_source_language_affix_search(search_run: SearchRun):
#     matching_words = do_affix_search(
#         search_run.internal_query,
#         source_language_affix_searcher(),
#     )
#     for word in matching_words:
#         search_run.add_result(
#             Result(
#                 word,
#                 source_language_affix_match=True,
#                 query_wordform_edit_distance=get_modified_distance(
#                     word.text, search_run.internal_query
#                 ),
#             )
#         )

# This is going to help with "cache.language_affix_searcher" in the top method
# Also, wherever WordForm is used, just use a direct DB call rather


def source_language_affix_searcher():
    """
    Return tuple of (text, id) pairs for all lemma Wordforms
    """
    # Connect to the DB
    conn = sqlite3.connect(os.path.realpath('../test_db.sqlite3'))

    c = conn.cursor()

    c.execute(""" SELECT text, id FROM lexicon_wordform where is_lemma = 1""")

    results = c.fetchall()

    # Slurp up all the results to prevent walking the database multiple times
    return AffixSearcher(tuple(results))


EXTRA_REPLACEMENTS = str.maketrans(
    {"ł": "l", "Ł": "L", "ɫ": "l", "Ɫ": "l", "ø": "o", "Ø": "O"}
)


def to_source_language_keyword(s: str) -> str:
    """Convert a source-language wordform to an indexable keyword

    Currently removes accents, and leading and trailing hyphens.

    There will be collisions but we could use edit distance to rank them.
    """
    s = s.lower()
    return (
        "".join(c for c in normalize("NFD", s)
                if unicodedata.combining(c) == 0)
        .translate(EXTRA_REPLACEMENTS)
        .strip("-"))
