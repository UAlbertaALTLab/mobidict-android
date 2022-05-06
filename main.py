from cgitb import text
import json
import sqlite3
import random
from kivymd.uix.label import MDLabel
from kivy.uix.label import Label
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
from kivy.uix.recycleview import RecycleView

from backend import get_main_page_results_list

initial_data_list = []

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
        print("OUTPUT:::", output_res)
        
        resultToPrint = output_res.copy()
        # self.results_print_str = "Hello"
        self.display_result_list(resultToPrint)
        # self.root.ids.result_label.text = output_res does the same thing as the above line
    
    def display_result_list(self, data_list):
        result_list_view = MDList()
        initial_result_list = []
        
        for data in data_list:
            
            title = data['lemma_wordform']['text'] if data['is_lemma'] else data['wordform_text']
            
            ic, emoji = data['lemma_wordform']['inflectional_category_plain_english'], data['lemma_wordform']['wordclass_emoji']
            
            emojis = ""
            subtitle = ""
            
            defs = []
            
            if emoji:
                emojis += emoji
            
            if ic and emoji:
                subtitle += "-"
            
            if ic:
                subtitle += ic
            
            flag = 1
                
            for definition in data['definitions']:
                defs.append(str(flag) + ". " + definition['text'])
                flag += 1
            print(defs)
            
            initial_result_list.append({'title': title, 'emojis': emojis, 'subtitle': subtitle, 'definitions': defs.copy()})
        
        root = App.get_running_app().root
        
        # root.ids.results_scroll_view.result_list_main.update_data(initial_result_list)
        root.ids.result_list_main.update_data(initial_result_list)
        
        # self.ids.results_scroll_view.clear_widgets()
        # self.ids.results_scroll_view.add_widget(result_list_view)

# Builder.load_file("morphodict.kv")

class ResultView(RecycleView):
    def __init__(self, **kwargs):
        super(ResultView, self).__init__(**kwargs)
        self.data = initial_data_list
    
    def update_data(self, data):
        self.data = data.copy()
        print("Damn, HERE!!", data)

class MorphodictApp(MDApp):
    def build(self):
        # self.theme_cls.theme_style = "Dark"  # "Light" - comment this on for dark theme.
        Window.clearcolor = (0.933, 1, 0.92, 1)


if __name__ == '__main__':
    MorphodictApp().run()
