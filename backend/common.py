# This file has some common functions used in all files globally.
import sqlite3
import os

from backend.WordForm import Wordform

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def make_wordform_dict(data):
    '''
    Given a dict, returns a WordForm object to be added.
    '''
    # Connect to the DB
    conn = sqlite3.connect(BASE_DIR + '/../main_db.sqlite3')

    conn.row_factory = sqlite3.Row

    c = conn.cursor()

    wfCopy = data

    while True:
        if wfCopy['is_lemma']:
            wfCopy['lemma'] = wfCopy.copy()
            break
        wfCopy['lemma'] = {}

        queryToSearch = f""" SELECT * FROM lexicon_wordform 
            WHERE id = \"{wfCopy['lemma_id']}\"
        """

        c.execute(queryToSearch)

        res = c.fetchone()
        wfFetched = dict(res)
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