from __future__ import annotations

import sqlite3
import os
import json

from core.typesCore import Result

from core.WordForm import rich_analyze_relaxed

from core.english_keyword_extraction import stem_keywords

from core.SearchRun import SearchRun
from core.WordForm import Wordform
from core.affix import to_source_language_keyword

from core.cree_lev_dist import get_modified_distance

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def fetch_results(search_run: SearchRun):
    
    # Connect to the DB
    conn = sqlite3.connect(BASE_DIR + '/../test_db.sqlite3')

    conn.row_factory = sqlite3.Row

    c = conn.cursor()
    
    fetch_results_from_target_language_keywords(search_run)

    fetch_results_from_source_language_keywords(search_run)

    # Use the spelling relaxation to try to decipher the query
    #   e.g., "atchakosuk" becomes "acâhkos+N+A+Pl" --
    #         thus, we can match "acâhkos" in the dictionary!
    fst_analyses = set(rich_analyze_relaxed(search_run.internal_query))

    print("Next DS:::", [a.tuple for a in fst_analyses])
    fst_analyses_list = [a.tuple for a in fst_analyses]

    query_list = []
    for analyses in fst_analyses_list:
        query_list.append(json.dumps([list(analyses.prefixes), analyses.lemma, list(analyses.suffixes)], ensure_ascii=False))
    print("FINAL QUERY LIST: ", tuple(query_list))
    
    queryToExecute = f""" SELECT * FROM lexicon_wordform
                    WHERE raw_analysis in {str(tuple(query_list))}
                """

    c.execute(queryToExecute)
    
    db_matches = c.fetchall()
    
    print("DB MATCHES:::", db_matches)
    
    for wf in db_matches:
        data = dict(wf)
        finalWordFormToAdd = make_wordform_dict(data)
        search_run.add_result(
            Result(
                finalWordFormToAdd,
                source_language_match=finalWordFormToAdd.text,
                query_wordform_edit_distance=get_modified_distance(
                    finalWordFormToAdd.text, search_run.internal_query
                ),
            )
        )

        # An exact match here means we’re done with this analysis.
        fst_analyses.discard(finalWordFormToAdd.analysis)

    # # fst_analyses has now been thinned by calls to `fst_analyses.remove()`
    # # above; remaining items are analyses which are not in the database,
    # # although their lemmas should be.
    # for analysis in fst_analyses:
    #     # When the user query is outside of paradigm tables
    #     # e.g. mad preverb and reduplication: ê-mâh-misi-nâh-nôcihikocik
    #     # e.g. Initial change: nêpât: {'IC+nipâw+V+AI+Cnj+3Sg'}

    #     normatized_form_for_analysis = strict_generator().lookup(analysis.smushed())
    #     if len(normatized_form_for_analysis) == 0:
    #         logger.error(
    #             "Cannot generate normative form for analysis: %s (query: %s)",
    #             analysis,
    #             search_run.internal_query,
    #         )
    #         continue

    #     # If there are multiple forms for this analysis, use the one that is
    #     # closest to what the user typed.
    #     normatized_user_query = min(
    #         normatized_form_for_analysis,
    #         key=lambda f: get_modified_distance(f, search_run.internal_query),
    #     )

    #     possible_lemma_wordforms = best_lemma_matches(
    #         analysis, Wordform.objects.filter(
    #             text=analysis.lemma, is_lemma=True)
    #     )

    #     for lemma_wordform in possible_lemma_wordforms:
    #         synthetic_wordform = Wordform(
    #             text=normatized_user_query,
    #             raw_analysis=analysis.tuple,
    #             lemma=lemma_wordform,
    #         )
    #         search_run.add_result(
    #             Result(
    #                 synthetic_wordform,
    #                 analyzable_inflection_match=True,
    #                 query_wordform_edit_distance=get_modified_distance(
    #                     search_run.internal_query,
    #                     normatized_user_query,
    #                 ),
    #             )
    #         )


def fetch_results_from_target_language_keywords(search_run):
    print("STEM keyword!!: ", stem_keywords(search_run.internal_query))

    stem_keys = stem_keywords(search_run.internal_query)

    # Connect to the DB
    conn = sqlite3.connect(BASE_DIR + '/../test_db.sqlite3')

    conn.row_factory = sqlite3.Row

    c = conn.cursor()

    for stemmed_keyword in stem_keys:

        print("Stemmed keyword: ", stemmed_keyword)

        queryToExecute = f""" SELECT * FROM lexicon_wordform INNER JOIN lexicon_targetlanguagekeyword
                    ON lexicon_targetlanguagekeyword.wordform_id = lexicon_wordform.id
                    WHERE lexicon_targetlanguagekeyword.text = \"{stemmed_keyword}\"
                """

        c.execute(queryToExecute)

        results = c.fetchall()
        for wordform in results:
            data = dict(wordform)
            print("Data dict ", data)

            finalWordFormToAdd = make_wordform_dict(data)

            search_run.add_result(
                Result(finalWordFormToAdd, target_language_keyword_match=[
                    stemmed_keyword])
            )

    conn.close()


inputDictTest = {'id': 1, 'x': 2, 'is_lemma': 0, 'lemma': {'id': 2, 'x': 3, 'is_lemma': 0, 'lemma': {
    'id': 3, 'x': 4, 'is_lemma': 1, 'lemma': {'id': 3, 'x': 4, 'is_lemma': 1}}}}


def make_wordform_dict(data):
    '''
    Given a dict, returns a WordForm object to be added.
    '''
    # Connect to the DB
    conn = sqlite3.connect(BASE_DIR + '/../test_db.sqlite3')

    conn.row_factory = sqlite3.Row

    c = conn.cursor()

    wfCopy = data

    while True:
        if wfCopy['is_lemma']:
            wfCopy['lemma'] = wfCopy.copy()
            print("Recursive calls made")
            break
        wfCopy['lemma'] = {}

        queryToSearch = f""" SELECT * FROM lexicon_wordform 
            WHERE id = \"{wfCopy['lemma_id']}\"
        """

        c.execute(queryToSearch)

        res = c.fetchone()
        wfFetched = dict(res)
        print("Fetched something!", wfFetched)
        wfCopy['lemma'] = wfFetched
        wfCopy = wfCopy['lemma']

    # finalDictToAdd = build_nested_wordform(wfCopy)
    finalWordFormToAdd = build_nested_wordform(data)
    return finalWordFormToAdd


def build_nested_wordform(inputDict):
    inputDictCopy = inputDict

    inputDictCopy = Wordform(inputDictCopy)
    inputDictToReturn = inputDictCopy

    while True:
        if inputDictCopy.is_lemma:
            # base case
            inputDictCopy.lemma = inputDictCopy
            break
        inputDictCopy.lemma = Wordform(inputDictCopy.lemma)
        inputDictCopy = inputDictCopy.lemma
    return inputDictToReturn


def fetch_results_from_source_language_keywords(search_run):

    keyword = to_source_language_keyword(search_run.internal_query)
    print("Inside #2: ", keyword, type(keyword))

    conn = sqlite3.connect(BASE_DIR + '/../test_db.sqlite3')

    conn.row_factory = sqlite3.Row

    c = conn.cursor()

    queryToExecute = f""" SELECT * FROM lexicon_sourcelanguagekeyword
                    WHERE text = \"{keyword}\"
                """

    c.execute(queryToExecute)

    results = c.fetchall()

    print("RESULTS!", results, len(results))

    for res in results:
        f_res = dict(res)

        queryToRun = f""" SELECT * FROM lexicon_wordform
                    WHERE id = \"{f_res['wordform_id']}\"
                """
        c.execute(queryToRun)

        wordform = c.fetchone()

        data = dict(wordform)

        finalWordFormToAdd = make_wordform_dict(data)

        search_run.add_result(
            Result(
                finalWordFormToAdd,
                source_language_keyword_match=[f_res['text']],
                query_wordform_edit_distance=get_modified_distance(
                    search_run.internal_query, finalWordFormToAdd.text
                ),
            )
        )
