import sqlite3


# def get_main_page_results_list(word):
#     # Create DB or connect to one
#     conn = sqlite3.connect("wordtest_db.db")

#     # Create a cursor
#     c = conn.cursor()

#     # Create a table
#     c.execute(""" SELECT * FROM words""")
#     res = c.fetchall()

#     # Commit our changes
#     conn.commit()

#     # Close the connection
#     conn.close()
#     return res


def get_main_page_results_list(query: str):
    return [1, 2, 3, 4]
