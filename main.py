# Release testing to see how much memory we currently occupy/for future purposes.
import webbrowser

from kivy.properties import ObjectProperty
from kivy.clock import Clock
from kivy.app import App
from kivy.lang import Builder
from kivy.utils import get_color_from_hex
from kivy.properties import StringProperty
from kivy.uix.widget import Widget
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.recycleview import RecycleView
from kivy.uix.screenmanager import ScreenManager
from kivy.uix.button import ButtonBehavior
from kivy.uix.label import Label
from kivy.core.window import Window

from kivymd.app import MDApp
from kivymd.theming import ThemableBehavior
from kivymd.uix.list import MDList, OneLineListItem, OneLineIconListItem, IconLeftWidget
from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard, MDSeparator
from kivymd.uix.tooltip import MDTooltip
from kivymd.uix.button import MDIconButton
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.menu import MDDropdownMenu

from cree_sro_syllabics import sro2syllabics

from backend import get_main_page_results_list

initial_data_list = []
initial_result_list = []

# To update a variable in .kv, you could go self.root.ids.{id}.text = ""

class ClickableLabel(ButtonBehavior, MDLabel):
    pass

class InfoTooltipButton(MDIconButton, MDTooltip):
    '''
    Class for the tooltip icon next to title
    '''
    pass

class WindowManager(ScreenManager):
    def __init__(self, **kwargs):
        super(WindowManager, self).__init__(**kwargs)
    
    def switch_to_result_screen(self, index):
        root = App.get_running_app().root
        root.ids.option_clicked.text = root.ids.result_list_main.data[index]['title']
        self.transition.direction = "left"
        self.current = "Result"
    
    def switch_back_home_screen(self):
        self.transition.direction = "right"
        self.current = "Home"


class HomeScreen(MDScreen):
    pass

class ResultScreen(MDScreen):
    pass


class ResultPageMainLayout(MDBoxLayout):
    pass

class ContentNavigationDrawer(MDBoxLayout):
    pass

class LabelSettingsItem(OneLineListItem):
    text = StringProperty()

def print_presentable_output(output):
    x = output.copy()
    counter = 1
    for y in x:
        print(f'''Output [{counter}]: ''', y)
        counter += 1
        print("-" * 80)

def replace_hats_to_lines_SRO(string):
    
    string = string.replace("ê", "ē")
    string = string.replace("î", "ī")
    string = string.replace("ô", "ō")
    string = string.replace("â", "ā")
    
    return string

class DrawerList(MDList):
    pass

class MainLayout(BoxLayout):
    def on_submit_word(self, widget= None):
        root = App.get_running_app().root
        current_query = root.ids.input_word.text
        
        if not current_query:
            # Empty query
            print("Empty query")
            return
        
        output_res = get_main_page_results_list(current_query)
        print_presentable_output(output_res)
        print("Output:", output_res)
        
        resultToPrint = output_res.copy()
        self.display_result_list(resultToPrint)
        # self.root.ids.result_label.text = output_res does the same thing as the above line
    
    def display_result_list(self, data_list):
        result_list_view = MDList()
        initial_result_list = []
        
        result_id_counter = 0
        
        app = App.get_running_app()
        
        for data in data_list:
            
            title = data['lemma_wordform']['text'] if data['is_lemma'] else data['wordform_text']
            
            ic, emoji = data['lemma_wordform']['inflectional_category_plain_english'], data['lemma_wordform']['wordclass_emoji']
            
            emojis = ""
            subtitle = ""
            
            defs = []
            
            if emoji:
                updated_emoji = emoji.replace("🧑🏽", "🧑")
                emojis += updated_emoji
            
            # if ic and emoji:
            #     subtitle += "-"
            
            if ic:
                subtitle += ic
            
            flag = 1
                
            for definition in data['definitions']:
                defs.append(str(flag) + ". " + definition['text'])
                flag += 1
            
            if app.index_selected == 2:
                # Syllabics selected
                title = sro2syllabics(title)
            elif app.index_selected == 1:
                # ēīōā selected
                title = replace_hats_to_lines_SRO(title)

            defsToPass = defs.copy()       
            initial_result_list.append({'index': result_id_counter, 
                                        'title': title, 
                                        'emojis': emojis, 
                                        'subtitle': subtitle,
                                        'friendly_linguistic_breakdown_head': data['friendly_linguistic_breakdown_head'],
                                        'friendly_linguistic_breakdown_tail': data['friendly_linguistic_breakdown_tail'],
                                        'relabelled_fst_analysis': data['relabelled_fst_analysis'],
                                        'definitions': defsToPass
                                        })
            
            result_id_counter += 1
        
        if len(initial_result_list) == 0:
            root = App.get_running_app().root
            initial_result_list.append({'index': -1, 'title': 'No results found!', 'definitions': [root.ids.input_word.text]})
        
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
    index = ObjectProperty()
    title = ObjectProperty()
    subtitle = ObjectProperty()
    emojis = ObjectProperty()
    friendly_linguistic_breakdown_head = ObjectProperty()
    friendly_linguistic_breakdown_tail = ObjectProperty()
    relabelled_fst_analysis = ObjectProperty()
    
    # Any new properties should be added above definitions for proper rendering
    definitions = ObjectProperty()
    
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(self.row_initialization, 0)
    
    def row_initialization(self, dp):
        if self.index != -1:
            title_icon_box_layout = BoxLayout()
            
            title_label = Label(text="[font=bjcrus.ttf][u][color=4C0121]" + self.title + "[/color][/u][/font]", markup=True)
            title_label._label.refresh()
            title_label = ClickableLabel(text="[font=bjcrus.ttf][u][color=4C0121]" + self.title + "[/color][/u][/font]", 
                                            markup=True,
                                            on_release=self.on_click_label,
                                            size_hint=(None, 1),
                                            width = title_label._label.texture.size[0] + 10)

            title_icon_box_layout.add_widget(title_label)
            
            if self.friendly_linguistic_breakdown_head or self.friendly_linguistic_breakdown_tail:
                tooltip_content = ""
                
                for chunk in self.relabelled_fst_analysis:
                    chunk_label = chunk['label']
                    if len(chunk_label) > 0:
                        chunk_label = chunk_label.replace("→", "->")
                    tooltip_content += chunk_label + "\n"
                
                if len(tooltip_content) > 0:
                    tooltip_content = tooltip_content[:-1]
                
                title_icon_box_layout.add_widget(InfoTooltipButton(icon="information", 
                                                                   tooltip_text= tooltip_content,
                                                                   user_font_size="20dp"))
            
            self.add_widget(title_icon_box_layout)
            
            # Add the line here.
            line_break = MDSeparator()
            
            self.add_widget(line_break)
            
            description_box_layout = BoxLayout()
            
            additional_emoji_margin = 0 if not self.emojis else 10
            
            # emoji_label = MDLabel(text="[size=14][font=NotoEmoji-Regular.ttf]" + self.emojis + "[/font][/size]", size_hint=(0.2, 1), markup=True)
            emoji_label = Label(text="[size=14][font=NotoEmoji-Regular.ttf]" + self.emojis + "[/font][/size]", markup=True)
            emoji_label._label.refresh()
            emoji_label = MDLabel(text="[size=14][font=NotoEmoji-Regular.ttf]" + self.emojis + "[/font][/size]", 
                                markup=True,
                                size_hint=(None, 1),
                                width=emoji_label._label.texture.size[0] + additional_emoji_margin)
        
            desc_label = MDLabel(text="[size=14]" + self.subtitle + "[/size]", markup=True)
            
            description_box_layout.add_widget(emoji_label)
            description_box_layout.add_widget(desc_label)
            
            self.add_widget(description_box_layout)
            
            for definition in self.definitions:
                definition_label = MDLabel(text=definition)
                self.add_widget(definition_label)
        
        else:
            root = App.get_running_app().root
            self.add_widget(MDLabel(text="[color=800000]" + "No results found for [b][i]<<" + root.ids.input_word.text + ">>" + "[/i][/b][/color]", 
                                    markup=True,
                                    halign= 'center'))
        
        self.bind(definitions = self.update_row)
    
    def update_row(self, *args):
        print("-"*100)
        
        print("=> title: ", self.title)
        print("=> subtitle: ", self.subtitle)
        print("=> emojis", self.emojis)
        print("=> definitions", self.definitions)
        
        self.clear_widgets()
        
        if self.index == -1:
            root = App.get_running_app().root
            self.add_widget(MDLabel(text="[color=800000]" + "No results found for [b][i]<<" + root.ids.input_word.text + ">>" + "[/i][/b][/color]", 
                                    markup=True,
                                    halign= 'center'))
            return
            
        title_icon_box_layout = BoxLayout()

        title_label = Label(text="[font=bjcrus.ttf][u][color=4C0121]" + self.title + "[/color][/u][/font]", markup=True)
        title_label._label.refresh()
        title_label = ClickableLabel(text="[font=bjcrus.ttf][u][color=4C0121]" + self.title + "[/color][/u][/font]", 
                                        markup=True,
                                        on_release=self.on_click_label,
                                        size_hint=(None, 1),
                                        width = title_label._label.texture.size[0] + 10)

        title_icon_box_layout.add_widget(title_label)
        
        if self.friendly_linguistic_breakdown_head or self.friendly_linguistic_breakdown_tail:
            tooltip_content = ""
            for chunk in self.relabelled_fst_analysis:
                chunk_label = chunk['label']
                if len(chunk_label) > 0:
                    chunk_label = chunk_label.replace("→", "->")
                tooltip_content += chunk_label + "\n"
            
            if len(tooltip_content) > 0:
                tooltip_content = tooltip_content[:-1]
            title_icon_box_layout.add_widget(InfoTooltipButton(icon="information", 
                                                               tooltip_text= tooltip_content,
                                                               user_font_size="20dp"))
        
        self.add_widget(title_icon_box_layout)
        
        # Add the line here.
        line_break = MDSeparator()
        
        self.add_widget(line_break)
        
        description_box_layout = BoxLayout()
        
        additional_emoji_margin = 0 if not self.emojis else 10
        
        emoji_label = Label(text="[size=14][font=NotoEmoji-Regular.ttf]" + self.emojis + "[/font][/size]", markup=True)
        emoji_label._label.refresh()
        emoji_label = MDLabel(text="[size=14][font=NotoEmoji-Regular.ttf]" + self.emojis + "[/font][/size]", 
                              markup=True,
                              size_hint=(None, 1),
                              width=emoji_label._label.texture.size[0] + additional_emoji_margin)
        
        desc_label = MDLabel(text="[size=14]" + self.subtitle + "[/size]", markup=True)
        
        description_box_layout.add_widget(emoji_label)
        description_box_layout.add_widget(desc_label)
        
        self.add_widget(description_box_layout)
        
        # definitions_box_layout = BoxLayout(orientation="vertical")
        
        for definition in self.definitions:
            definition_label = MDLabel(text=definition)
            self.add_widget(definition_label)
            # definitions_box_layout.add_widget(definition_label)
        
    # This method works if you want to detect a touch anywhere in the entire widget    
    # def on_touch_down(self, touch):
    #     if self.collide_point(*touch.pos):
    #         # The touch has occurred inside the widgets area.
    #         print("CLICKED, index: ", self.index)
    #         root = App.get_running_app().root
    #         root.ids.screen_manager.switch_to_result_screen(self.index)
            
    #     return super(ResultWidget, self).on_touch_down(touch)
        
    def on_click_label(self, touch):
        root = App.get_running_app().root
        root.ids.screen_manager.switch_to_result_screen(self.index)
    

class MorphodictApp(MDApp):
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.menu = None
        self.index_selected = 0
    
    def build(self):
        # self.theme_cls.theme_style = "Dark"  # "Light" - comment this on for dark theme.
        Window.clearcolor = (0.933, 1, 0.92, 1)
        
        # Label Settings Menu
        label_settings_items = [{'index': 0, 
                                 'text': "SRO(êîôâ)", 
                                 "viewclass": "LabelSettingsItem", 
                                 "on_release": lambda x=f"SRO(êîôâ)": self.set_item(x),
                                 "text_color": (0, 0, 1, 1)},
                                {'index': 1, 'text': "SRO(ēīōā)", 
                                 "viewclass": "LabelSettingsItem", 
                                 "on_release": lambda x=f"SRO(ēīōā)": self.set_item(x),
                                 "text_color": (0, 0, 0, 1)},
                                {'index': 2, 
                                 'text': "Syllabics", 
                                 "viewclass": "LabelSettingsItem", 
                                 "on_release": lambda x=f"Syllabics": self.set_item(x),
                                 "text_color": (0, 0, 0, 1)}]
        
        self.menu = MDDropdownMenu(
            caller=self.root.ids.label_settings_dropdown,
            items=label_settings_items,
            width_mult=4,
        )
    
    def set_item(self, text_item):
        if self.root.ids.label_settings_dropdown.current_item == text_item:
            # Same option chosen, don't do anything
            return
        label_settings_items = [{'index': 0, 
                                 'text': "SRO(êîôâ)", 
                                 "viewclass": "LabelSettingsItem", 
                                 "on_release": lambda x=f"SRO(êîôâ)": self.set_item(x),
                                 "text_color": (0, 0, 0, 1)},
                                {'index': 1, 'text': "SRO(ēīōā)", 
                                 "viewclass": "LabelSettingsItem", 
                                 "on_release": lambda x=f"SRO(ēīōā)": self.set_item(x),
                                 "text_color": (0, 0, 0, 1)},
                                {'index': 2, 
                                 'text': "Syllabics", 
                                 "viewclass": "LabelSettingsItem", 
                                 "on_release": lambda x=f"Syllabics": self.set_item(x),
                                 "text_color": (0, 0, 0, 1)}]
        if text_item == "Syllabics":
            label_settings_items[2]["text_color"] = (0, 0, 1, 1)
            self.index_selected = 2
        elif text_item == "SRO(ēīōā)":
            label_settings_items[1]["text_color"] = (0, 0, 1, 1)
            self.index_selected = 1
        else:
            label_settings_items[0]["text_color"] = (0, 0, 1, 1)
            self.index_selected = 0
        
        self.menu.items = label_settings_items
        self.root.ids.label_settings_dropdown.set_item(text_item)
        self.root.ids.main_box_layout.on_submit_word()
        self.menu.dismiss()
    
    def on_start(self):
        # Preload these things
        
        def on_release_help(arg):
            webbrowser.open("https://altlab.ualberta.ca/itwewina/#help")
            
        def on_release_settings(arg):
            print("Settings pressed!")
        
        drawer_items_list = [{'text': 'Help', 'icon': "help-circle", 'callback': on_release_help},
                             {'text': 'Legend of Abbreviations', 'icon': 'text-box-outline', 'callback': on_release_help},
                             {'text': 'About', 'icon': "account-group", 'callback': on_release_help},
                             {'text': 'Contact us', 'icon': "email", 'callback': on_release_help},
                             {'text': 'Settings', 'icon': "cog", 'callback': on_release_settings}]
        
        for drawer_item in drawer_items_list:
            row_item = OneLineIconListItem(text=drawer_item['text'], on_release=drawer_item['callback'])
            row_item.add_widget(IconLeftWidget(icon=drawer_item['icon']))
            self.root.ids.navigation_drawer_list.add_widget(row_item)
        return super().on_start()


if __name__ == '__main__':
    MorphodictApp().run()
