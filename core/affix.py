

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

def fetch_source_language_lemmas_with_ids():
    """
    Return tuple of (text, id) pairs for all lemma Wordforms
    """
    # Slurp up all the results to prevent walking the database multiple times
    return tuple(Wordform.objects.filter(is_lemma=True).values_list("text", "id"))
