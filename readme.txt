To start the code,

(Assumes virtualenv is installed)- if not, go "pip3 install virtualenv"

1. Make the virtualenv using virtualenv venv
2. Type 'source venv/bin/activate'
3. Change directory into the project folder (mobidict-android) and run "pip3 install -r requirements.txt"
4. Once you clone the repo, the database file would be missing. Generate the DB from morphodict repository the usual way and copy that to the app root directory (where main.py is present), and rename it to "main_db.sqlite3".
5. Run with the ">" button OR python3 main.py in shell.

To deactivate venv, type 'deactivate'. I am using virtualenv for virtual env.

Troubleshooting:
- If you encounter the error "Could not find core.SearchRun", just rename the searchRun.py file in the core folder to "SearchRun.py". (This should be solved soon)


Resources:
1. https://www.youtube.com/watch?v=X2MkC1ru3cQ&list=PLCC34OHNcOtpz7PJQ7Tv7hqFBP_xDDjqg&index=56
2. https://www.youtube.com/watch?v=l8Imtec4ReQ&t=585s
3. https://kivycoder.com/using-sqlite3-database-with-kivy-python-kivy-gui-tutorial-55/
4. https://kivymd.readthedocs.io/en/latest/getting-started/
