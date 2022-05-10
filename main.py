from functools import partial
import json
import sqlite3
import random
import emoji
from kivymd.uix.label import MDLabel
from kivy.properties import ObjectProperty
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
from kivy.clock import Clock

from backend import get_main_page_results_list

initial_data_list = []
initial_result_list = []

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
                updated_emoji = emoji.replace("🧑🏽", "🧑")
                emojis += updated_emoji
            
            if ic and emoji:
                subtitle += "-"
            
            if ic:
                subtitle += ic
            
            flag = 1
                
            for definition in data['definitions']:
                defs.append(str(flag) + ". " + definition['text'])
                flag += 1

            defsToPass = defs.copy()
            
            initial_result_list.append({'title': title, 'emojis': emojis, 'subtitle': subtitle, 'definitions': defsToPass})
        
        root = App.get_running_app().root
        
        print("INITIAL RES LIST::", initial_result_list)
        
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
        # root = App.get_running_app().root
        # root.ids.result_list_main.refresh_from_data()
        self.refresh_from_data()

class ResultWidget(BoxLayout):
    title = ObjectProperty()
    subtitle = ObjectProperty()
    emojis = ObjectProperty()
    definitions = ObjectProperty()
    
    # BUG: When you search a new word, the results currently don't get updated.
    
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(self.row_initialization, 0)
    
    def row_initialization(self, dp):
        self.add_widget(MDLabel(text="[u][color=4C0121]" + self.title + "[/color][/u]", markup=True))
        
        description_box_layout = BoxLayout()
        
        emoji_label = MDLabel(text="[size=14][font=NotoEmoji-Regular.ttf]" + self.emojis + "[/font][/size]", size_hint=(0.2, 1), markup=True)
        desc_label = MDLabel(text="[size=14]" + self.subtitle + "[/size]", markup=True)
        
        description_box_layout.add_widget(emoji_label)
        description_box_layout.add_widget(desc_label)
        
        self.add_widget(description_box_layout)
        
        definitions_box_layout = BoxLayout(orientation="vertical")
        
        for definition in self.definitions:
            definition_label = MDLabel(text=definition)
            # self.add_widget(definition_label)
            definitions_box_layout.add_widget(definition_label)
        
        self.add_widget(definitions_box_layout)
        
        self.bind(definitions = self.update_row)
    
    def update_row(self, *args):
        print("-"*100)
        
        print("=> title: ", self.title)
        print("=> subtitle: ", self.subtitle)
        print("=> emojis", self.emojis)
        print("=> definitions", self.definitions)
        
        self.clear_widgets()
        
        self.add_widget(MDLabel(text="[u][color=4C0121]" + self.title + "[/color][/u]", markup=True))
        
        description_box_layout = BoxLayout()
        
        emoji_label = MDLabel(text="[size=14][font=NotoEmoji-Regular.ttf]" + self.emojis + "[/font][/size]", size_hint=(0.2, 1), markup=True)
        desc_label = MDLabel(text="[size=14]" + self.subtitle + "[/size]", markup=True)
        
        description_box_layout.add_widget(emoji_label)
        description_box_layout.add_widget(desc_label)
        
        self.add_widget(description_box_layout)
        
        definitions_box_layout = BoxLayout()
        
        for definition in self.definitions:
            definition_label = MDLabel(text=definition)
            self.add_widget(definition_label)
        
        
        

class MorphodictApp(MDApp):
    def build(self):
        # self.theme_cls.theme_style = "Dark"  # "Light" - comment this on for dark theme.
        Window.clearcolor = (0.933, 1, 0.92, 1)


if __name__ == '__main__':
    MorphodictApp().run()
