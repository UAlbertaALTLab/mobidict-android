import sqlite3
import os


def do_source_language_affix_search(search_run: core.SearchRun):
    matching_words = do_affix_search(
        search_run.internal_query,
        cache.source_language_affix_searcher,
    )
    for word in matching_words:
        search_run.add_result(
            Result(
                word,
                source_language_affix_match=True,
                query_wordform_edit_distance=get_modified_distance(
                    word.text, search_run.internal_query
                ),
            )

# This is going to help with "cache.language_affix_searcher" in the top method
# Also, wherever WordForm is used, just use a direct DB call rather
def fetch_source_language_lemmas_with_ids():
    """
    Return tuple of (text, id) pairs for all lemma Wordforms
    """
    # Connect to the DB
    conn=sqlite3.connect(os.path.realpath('../test_db.sqlite3'))

    c=conn.cursor()

    # c.execute(""" SELECT * FROM words""")
#     res = c.fetchall()

    # Slurp up all the results to prevent walking the database multiple times
    return tuple(Wordform.objects.filter(is_lemma=True).values_list("text", "id"))
