# Welcome to Mobidict

## Steps to run the app locally

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

## Steps to release the app from scratch

1. Make a new folder for the build.
2. Clone the mobidict-android repository.
3. Create a virtualenv by "virtualenv [name of environment]". For eg. "virtualenv mobidict"
4. Activate the environment by source "mobidict/bin/activate"
5. Make the DB the usual way from morphodict and take the test_db.sqlite3 file and paste it in the root directory of the project. (mobidict-android/) where main.py is found.
6. Rename the db to main_db.sqlite3
7. Run the app using "python3 main.py" from the root directory. 

Now the app should run successfully. Only proceed once it is running properly.

8. To continue the build, deactivate the virtualenv by "deactivate"
9. Follow the steps on https://buildozer.readthedocs.io/en/latest/ (installation) to install all dependencies required to run buildozer.
10. Once it's installed using all the dependencies, go "buildozer init" in the root directory. This should create buildozer.spec.
11. Remove all the contents of buildozer.spec and paste everything from the buildozer.spec on branch release-v5 on mobidict-android. (I have modified it to include all dependencies we are using in the app)
12. Lastly, go "buildozer -v android debug" to make the .apk file.
13. To test it, we would need a x86_64 environment. So make sure when you use a virtual emulator from Android Studio, it has the environment x86_64 set up. 
14. Just drag the .apk file onto the emulator to test. 

15. Alternatively, you can also use a physical device connected to your desktop/laptop - just follow the steps on https://buildozer.readthedocs.io/en/latest/quickstart.html

16. Instead of buildozer -v android debug, we could also go "buildozer -v android debug deploy run logcat" if a device is connected (make sure the developer mode is enabled and so is USB debugging. Many times, just turning the USB debugging off and on solves the unauthorized device problem.) To clean before running the latter command, one can go "buildozer android clean" to clean and refresh the build or if one wants to refresh a recipe, they can go "buildozer android p4a -- clean_recipe_build [recipe name]".

Notes and Resources for Troubleshooting the build:
- I came across weird errors while building the app with "buildozer -v android debug" - so this website helped me:
https://vucavucalife.com/build-apk-with-buildozer-and-install-to-androidemu-on-macos-12-4-m1-macbook/
Note that it's in Chinese and you can convert it to an English page to understand.

- I was using the Python version 3.9.12 - note that this is extremely important to work with the current buildozer.spec - because if you have any later version, the build may/may not work - and you will need to change the buildozer.spec requirements (python3, hostpython3)
- In case pip3 install buildozer gives problems on step 10, follow the buildozer steps on https://kivy.org/doc/stable/guide/packaging-android.html. This helped me make buildozer work on terminal.

### Errors encountered while packaging the app
1. dlopen failed - [x].so has a bad ELF magic. This usually means the library you have added needs a custom recipe. Add this recipe to .buildozer/android/platform/python-for-android/pythonforandroid/recipes/[name of library]/__init__.py - The recipe template looks like: https://pastebin.com/MHd0FdH0. Don't forget to add the source files from github (you can just git clone the source files from the home directory of that project) in the path specified. The same needs to have a setup.py - so that once you have cloned everything into the [project folder name] in the root directory of our main project, just go into that folder and go 'python3 setup.py install'. This will "cythonize" your library.
2. No module named [x]: This is pretty straightforward. This usually means you are missing this library name in the requirements in the buildozer.spec file.
