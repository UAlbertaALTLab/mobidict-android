from tkinter import N
from hfst_optimized_lookup import TransducerFile, Analysis
from functools import cache

from typing import Dict, Literal, Union

from general import STRICT_ANALYZER_FST_FILENAME, RELAXED_ANALYZER_FST_FILENAME, STRICT_GENERATOR_FST_FILENAME

FST_DIR = "resourcesFST"

WordformKey = Union[int, tuple[str, str]]


class Wordform:
    def __init__(self, inputDict=None) -> None:
        text = ""
        raw_analysis = ""
        fst_lemma = ""
        paradigm = ""
        is_lemma = ""
        lemma = ""
        slug = ""
        linguist_info = None
        import_hash = None

        if inputDict is not None:
            text = inputDict['text']
            raw_analysis = inputDict['raw_analysis']
            fst_lemma = inputDict['fst_lemma']
            paradigm = inputDict['paradigm']
            is_lemma = inputDict['is_lemma']
            lemma = inputDict['lemma']
            slug = inputDict['slug']
            linguist_info = inputDict['linguist_info']
            import_hash = inputDict['import_hash']

    def __str__(self):
        return self.text

    def __repr__(self):
        cls_name = type(self).__name__
        return f"<{cls_name}: {self.text} {self.analysis}>"

    @property
    def analysis(self):
        if self.raw_analysis is None:
            return None
        return RichAnalysis(self.raw_analysis)

    @property
    def key(self) -> WordformKey:
        """A value to check if objects represent the ‘same’ wordform

        Works even if the objects are unsaved.
        """
        if self.slug is not None:
            return self.slug
        if self.id is not None:
            return self.id
        return (self.text, self.analysis)


def strict_generator():
    return TransducerFile(FST_DIR / STRICT_GENERATOR_FST_FILENAME)


def relaxed_analyzer():
    return TransducerFile(FST_DIR / RELAXED_ANALYZER_FST_FILENAME)


def strict_analyzer():
    return TransducerFile(FST_DIR / STRICT_ANALYZER_FST_FILENAME)


def rich_analyze_relaxed(text):
    return list(
        RichAnalysis(r) for r in relaxed_analyzer().lookup_lemma_with_affixes(text)
    )


class RichAnalysis:
    """The one true FST analysis class.

    Put all your methods for dealing with things like `PV/e+nipâw+V+AI+Cnj+3Pl`
    here.
    """

    def __init__(self, analysis):
        if isinstance(analysis, Analysis):
            self._tuple = analysis
        elif (isinstance(analysis, list) or isinstance(analysis, tuple)) and len(
            analysis
        ) == 3:
            prefix_tags, lemma, suffix_tags = analysis
            self._tuple = Analysis(
                prefixes=tuple(prefix_tags), lemma=lemma, suffixes=tuple(suffix_tags)
            )
        else:
            raise Exception(f"Unsupported argument: {analysis=!r}")

    @property
    def tuple(self):
        return self._tuple

    @property
    def lemma(self):
        return self._tuple.lemma

    @property
    def prefix_tags(self):
        return self._tuple.prefixes

    @property
    def suffix_tags(self):
        return self._tuple.suffixes

    def generate(self):
        return strict_generator().lookup(self.smushed())

    def smushed(self):
        return "".join(self.prefix_tags) + self.lemma + "".join(self.suffix_tags)

    def tag_set(self):
        return set(self.suffix_tags + self.prefix_tags)

    def tag_intersection_count(self, other):
        """How many tags does this analysis have in common with another?"""
        if not isinstance(other, RichAnalysis):
            raise Exception(f"Unsupported argument: {other=!r}")
        return len(self.tag_set().intersection(other.tag_set()))

    def __iter__(self):
        """Allows doing `head, _, tail = rich_analysis`"""
        return iter(self._tuple)

    def __hash__(self):
        return hash(self._tuple)

    def __eq__(self, other):
        if not isinstance(other, RichAnalysis):
            return NotImplemented
        return self._tuple == other.tuple

    def __repr__(self):
        return f"RichAnalysis({[self.prefix_tags, self.lemma, self.suffix_tags]!r})"
