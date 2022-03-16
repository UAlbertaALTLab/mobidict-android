import re
import sqlite3
import snowballstemmer
from typing import Set
from core.runner import search
# def get_main_page_results_list(word):
#     # Create DB or connect to one
#     conn = sqlite3.connect("wordtest_db.db")

#     # Create a cursor
#     c = conn.cursor()

#     c.execute(""" SELECT * FROM words""")
#     res = c.fetchall()

#     # Commit our changes
#     conn.commit()

#     # Close the connection
#     conn.close()
#     return res


def get_main_page_results_list(query: str):
    # user_query is the input word from the user
    user_query = query[:]
    print("USER QUERY: ", user_query)

    dict_source = None

    search_run = None

    if user_query:
        include_auto_definitions = False
        # TODO: Need to get this working
        search_run = search_with_affixes(
            user_query,
            include_auto_definitions=include_auto_definitions,
        )

    return search_run


def search_with_affixes(query: str, include_auto_definitions=False):
    """
    Search for wordforms matching:
     - the wordform text
     - the definition keyword text
     - affixes of the wordform text
     - affixes of the definition keyword text
    """

    return search(query=query, include_auto_definitions=include_auto_definitions)
