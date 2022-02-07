import imp
import sqlite3
import random
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.core.window import Window
from kivy.properties import StringProperty
from kivymd.app import MDApp

from backend import get_main_page_results_list

# To update a variable in .kv, you could go self.root.ids.{id}.text = ""


class MainLayout(BoxLayout):
    results_print_str = StringProperty("")

    def on_submit_word(self, widget):
        # To get access to the input, you could also go TextinputId.text directly.
        output_res = get_main_page_results_list(widget.text)
        x = random.randint(0, 2)
        print(x)
        print(output_res)
        self.results_print_str = str(output_res[x])
        # self.root.ids.result_label.text = output_res does the same thing as the above line


# Builder.load_file("morphodict.kv")


class MorphodictApp(App):
    def build(self):
        Window.clearcolor = (0.933, 1, 0.92, 1)

        # Create DB or connect to one
        conn = sqlite3.connect("wordtest_db.db")

        # Create a cursor
        c = conn.cursor()

        # Create a table
        c.execute(""" CREATE TABLE if not exists words(name text) """)

        # Add sample data
        c.execute(""" INSERT into words VALUES (:first) """,
                  {'first': "Talking"})

        c.execute(""" INSERT into words VALUES (:first) """,
                  {'first': "Walking"})

        c.execute(""" INSERT into words VALUES (:first) """,
                  {'first': "Running"})

        # Commit our changes
        conn.commit()

        # Close the connection
        conn.close()

        return MainLayout()

# class MorphodictApp(MDApp):
#     def build(self):
#         self.theme_cls.theme_style = "Light"
#         self.theme_cls.primary_palette = "BlueGray"
#         return MainLayout()


if __name__ == '__main__':
    MorphodictApp().run()
