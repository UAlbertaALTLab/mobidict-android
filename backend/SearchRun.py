from backend.query import Query

from typing import Iterable, Optional, Union, TypeVar

import backend.typesCore as types

from backend.preferences import AnimateEmoji, DisplayMode
from backend.presentation import PresentationResult

WordformKey = Union[int, tuple[str, str]]


T = TypeVar("T")


class SearchRun:
    """
    Holds a query and gathers results into a result collection.

    This class does not directly perform searches; for that, see runner.py.
    Instead, it provides an API for various search methods to access the query,
    and to add results to the result collection for future ranking.
    """

    def __init__(self, query: str, include_auto_definitions=None):
        self.query = Query(query)
        self.include_auto_definitions = first_non_none_value(
            self.query.auto, include_auto_definitions, default=False
        )
        self._results = {}
        self.sort_function = None

    include_auto_definition: bool
    _results: dict[WordformKey, types.Result]
    VerboseMessage = dict[str, str]
    _verbose_messages: list[VerboseMessage]

    def add_result(self, result: types.Result):
        if not isinstance(result, types.Result):
            raise TypeError(f"{result} is {type(result)}, not Result")
        key = result.wordform.key
        if key in self._results:
            self._results[key].add_features_from(result)
        else:
            self._results[key] = result

    def has_result(self, result: types.Result):
        return result.wordform.key in self._results

    def remove_result(self, result: types.Result):
        del self._results[result.wordform.key]

    def unsorted_results(self) -> Iterable[types.Result]:
        return self._results.values()

    def sorted_results(self) -> list[types.Result]:
        results = list(self._results.values())
        for r in results:
            r.assign_default_relevance_score()

        if self.sort_function is not None:
            results.sort(key=self.sort_function)
        else:
            results.sort()
        return results

    def presentation_results(
        self,
        display_mode=DisplayMode.default,
        animate_emoji=AnimateEmoji.default,
        dict_source=None,
    ) -> list[PresentationResult]:
        results = self.sorted_results()
        # prefetch_related_objects(
        #     [r.wordform for r in results],
        #     "lemma__definitions__citations",
        #     "definitions__citations",
        # )
        return [
            PresentationResult(
                r,
                search_run=self,
                display_mode=display_mode,
                animate_emoji=animate_emoji,
                dict_source=dict_source,
            )
            for r in results
        ]

    def serialized_presentation_results(
        self,
        display_mode=DisplayMode.default,
        animate_emoji=AnimateEmoji.default,
        dict_source=None,
    ):
        results = self.presentation_results(
            display_mode=display_mode,
            animate_emoji=animate_emoji,
            dict_source=dict_source,
        )
        serialized = [r.serialize() for r in results]

        def has_definition(r):
            # does the entry itself have a definition?
            if r["definitions"]:
                return True
            # is it a form of a word that has a definition?
            if "lemma_wordform" in r:
                if "definitions" in r["lemma_wordform"]:
                    if r["lemma_wordform"]["definitions"]:
                        return True
            return False

        return [r for r in serialized if has_definition(r)]

    def add_verbose_message(self, message=None, **messages):
        """
        Add any arbitrary JSON-serializable data to be displayed to the user at the
        top of the search page, if a search is run with verbose:1.

        Protip! Use keyword arguments as syntactic sugar for adding a dictionary, e.g.,

            search_run.add_verbose_message(foo="bar")

        Will appear as:

        [
            {"foo": "bar"}
        ]
        """
        if message is None and not messages:
            raise TypeError("must provide a message or messages")

        if message is not None:
            self._verbose_messages.append(message)
        if messages:
            self._verbose_messages.append(messages)

    @property
    def verbose_messages(self):
        return self._verbose_messages

    @property
    def internal_query(self):
        return self.query.query_string

    def __repr__(self):
        return f"SearchRun<query={self.query!r}>"


def first_non_none_value(*l: T, default: Optional[T] = None) -> T:
    """
    Return the first item in the iterable that is not None.

    Handy for selecting the first set value from a bunch of `Optional`s. A
    default value may also be explicitly specified.

    >>> first_non_none_value('a', 'b')
    'a'
    >>> first_non_none_value(None, False, True)
    False
    >>> first_non_none_value(None, None, None, default='b')
    'b'
    """
    try:
        return next(a for a in l if a is not None)
    except StopIteration:
        if default is not None:
            return default
        raise Exception("only None values were provided")
