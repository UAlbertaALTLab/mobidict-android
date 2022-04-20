from cgitb import text
import json
import sqlite3
import random
from kivymd.uix.label import MDLabel
from sys import displayhook
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.widget import Widget
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.core.window import Window
from kivy.properties import StringProperty
from kivymd.app import MDApp
from kivymd.uix.list import OneLineListItem, MDList, OneLineListItem, TwoLineListItem

from backend import get_main_page_results_list

# To update a variable in .kv, you could go self.root.ids.{id}.text = ""

def print_presentable_output(output):
    x = output.copy()
    counter = 1
    for y in x:
        print(f'''Output [{counter}]: ''', y)
        counter += 1
        print("-"*80)
        

class MainLayout(BoxLayout):
    # results_print_str = StringProperty("")

    def on_submit_word(self, widget):
        # To get access to the input, you could also go TextinputId.text directly.
        output_res = get_main_page_results_list(widget.text)
        print_presentable_output(output_res)
        print("OUTPUT::::::::", output_res)
        
        resultToPrint = output_res.copy()
        # self.results_print_str = "Hello"
        self.display_result_list(resultToPrint)
        # self.root.ids.result_label.text = output_res does the same thing as the above line
    
    def display_result_list(self, data_list):
        result_list_view = MDList()
        
        for data in data_list:
            
            def_list = MDList()
            
            title = data['lemma_wordform']['text'] if data['is_lemma'] else data['wordform_text']
            
            item = OneLineListItem(text = title)
            
            result_list_view.add_widget(item)
            
            for definition in data['lemma_wordform']['definitions']:
                def_row =  MDLabel(text = definition['text'])
                def_list.add_widget(def_row)
            
            result_list_view.add_widget(def_list)
            
            def_list.clear_widgets()
        
        self.ids.results_scroll_view.clear_widgets()
        self.ids.results_scroll_view.add_widget(result_list_view)

# Builder.load_file("morphodict.kv")


class MorphodictApp(MDApp):
    def build(self):
        Window.clearcolor = (0.933, 1, 0.92, 1)

        # # Create DB or connect to one
        # conn = sqlite3.connect("wordtest_db.db")

        # # Create a cursor
        # c = conn.cursor()

        # # Create a table
        # c.execute(""" CREATE TABLE if not exists words(name text) """)

        # # Add sample data
        # c.execute(""" INSERT into words VALUES (:first) """,
        #           {'first': "Talking"})

        # c.execute(""" INSERT into words VALUES (:first) """,
        #           {'first': "Walking"})

        # c.execute(""" INSERT into words VALUES (:first) """,
        #           {'first': "Running"})

        # # Commit our changes
        # conn.commit()

        # # Close the connection
        # conn.close()

        return MainLayout()

# class MorphodictApp(MDApp):
#     def build(self):
#         self.theme_cls.theme_style = "Light"
#         self.theme_cls.primary_palette = "BlueGray"
#         return MainLayout()


if __name__ == '__main__':
    MorphodictApp().run()
