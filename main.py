from email.policy import default
from math import ceil
import webbrowser
import threading
import paradigm_panes
import os

from kivy.properties import ObjectProperty
from kivy.clock import Clock
from kivy.app import App
from kivy.lang import Builder
from kivy.utils import get_color_from_hex
from kivy.metrics import dp
from kivy.properties import StringProperty, BooleanProperty, NumericProperty
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.stacklayout import StackLayout
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.screenmanager import ScreenManager
from kivy.uix.button import ButtonBehavior
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.core.audio import SoundLoader

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
from kivymd.uix.spinner import MDSpinner
from kivymd.uix.selectioncontrol import MDSwitch
from kivymd.toast import toast
from kivymd.uix.expansionpanel import MDExpansionPanel, MDExpansionPanelTwoLine
from kivy.graphics import Rectangle, Color

from cree_sro_syllabics import sro2syllabics

from backend import get_main_page_results_list
from api.api import get_sound
from general import SOUND_FILE_NAME, LEGEND_OF_ABBREVIATIONS_TEXT, CONTACT_US_TEXT, HELP_CONTACT_FORM_LINK, ABOUT_TEXT_SOURCE_MATERIALS, ABOUT_TEXT_CREDITS
from core.frontend.relabelling import relabel

initial_data_list = []
initial_result_list = []

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class ClickableLabel(ButtonBehavior, MDLabel):
    pass

class ClickableImage(ButtonBehavior, Image):
    pass

class InfoTooltipButton(MDIconButton, MDTooltip):
    '''
    Class for the tooltip icon next to title
    '''
    pass

class ModeSwitch(MDSwitch):
    def change_mode(self):
        app = App.get_running_app()
        if self.active:
            app.linguistic_mode = True
        else:
            app.linguistic_mode = False
        app.root.ids.main_box_layout.on_submit_word()
        second_page_population_list = app.root.ids.specific_result_main_list
        app.root.ids.specific_result_main_list.populate_page( second_page_population_list.title,
                                                              second_page_population_list.emojis, 
                                                              app.newest_result_list[app.last_result_list_index_click]['subtitle'] if app.last_result_list_index_click is not None else "",
                                                              second_page_population_list.default_title,
                                                              second_page_population_list.definitions)


class EmojiSwitch(MDSwitch):
    def change_mode(self):
        print("Emojis display changed")
        app = App.get_running_app()
        if self.active:
            app.display_emoji_mode = True
        else:
            app.display_emoji_mode = False
        
        app.root.ids.main_box_layout.on_submit_word()
        second_page_population_list = app.root.ids.specific_result_main_list
        app.root.ids.specific_result_main_list.populate_page( second_page_population_list.title,
                                                              second_page_population_list.emojis, 
                                                              app.newest_result_list[app.last_result_list_index_click]['subtitle'] if app.last_result_list_index_click is not None else "",
                                                              second_page_population_list.default_title,
                                                              second_page_population_list.definitions)

class ParadigmLabelContent(MDBoxLayout):
    '''Custom content for Expandible panels.'''
    
    def __init__(self, data, **kwargs ):
        super().__init__(**kwargs)
        self.data = data
        
        self.orientation = 'vertical'
        self.padding = "20dp"
        self.spacing = "20dp"
        
        Clock.schedule_once(self.populate_content, 0)
        
    def populate_content(self, args):
        '''
        Population of each expansion panel
        '''
        
        root = App.get_running_app().root
        app = App.get_running_app()
        
        self.add_widget(MDLabel(text = "", size_hint = (1, 0.1)))
        
        layout_row_list = MDList()
        
        paradigm_parameter = ["english", "linguistic", "source_language"]
        
        print("Current PARADIGM pane: ", self.data)
        
        # within_paradigm_scrollview = ScrollView(size_hint=(1, None), height="400dp")
        
        # Prepare the paradigm data and add it to the screen
        for row in self.data['tr_rows']:
            row_box_layout = MDBoxLayout(height="40dp", size_hint = (1, None))
            if row['is_header']:
                txt_label = relabel(row['label'], paradigm_parameter[app.index_selected_paradigms])
                
                if app.index_selected_paradigms == 2:
                    # source language labels
                    txt_label = app.get_syllabics_sro_correct_label(txt_label)
                    txt_label = "[font=bjcrus.ttf]" + txt_label + "[/font]"
                
                txt_label = "[i]" + txt_label + "[/i]"
                
                row_box_layout.add_widget(Label(text = txt_label, 
                                                markup = True,
                                                size_hint = (0.05, None), 
                                                pos_hint = {'center_x': 0.5}, 
                                                color= (0, 0, 0, 1)))
            else:
                for cell in row['cells']:
                    if cell['should_suppress_output']:
                        continue
                    elif cell['is_label']:
                        paradigm_label_text = relabel(cell['label'], paradigm_parameter[app.index_selected_paradigms])

                        if app.index_selected_paradigms == 2:
                            paradigm_label_text = app.get_syllabics_sro_correct_label(paradigm_label_text)
                            paradigm_label_text = "[font=bjcrus.ttf]" + paradigm_label_text + "[/font]"
                        
                        paradigm_label_text = "[i]" + paradigm_label_text + "[/i]"
                        
                        row_box_layout.add_widget(Label(text = paradigm_label_text,
                                                        markup = True,
                                                        size_hint = (0.05, None), 
                                                        pos_hint = {'center_x': 0.5}, 
                                                        color= (0, 0, 0, 1)))
                    elif cell['is_missing'] or cell['is_empty']:
                        row_box_layout.add_widget(Label(text = "--", 
                                                    size_hint = (0.05, None), 
                                                    pos_hint = {'center_x': 0.5}, 
                                                    color= (0, 0, 0, 1)))
                    else:
                        txt_label = app.get_syllabics_sro_correct_label(cell['inflection'])
                        row_box_layout.add_widget(Label(text = txt_label,
                                                    size_hint = (0.05, None), 
                                                    pos_hint = {'center_x': 0.5}, 
                                                    color= (0, 0, 0, 1),
                                                    font_name = 'bjcrus.ttf'))
                
            layout_row_list.add_widget(row_box_layout)
        self.add_widget(layout_row_list)
        # self.add_widget(within_paradigm_scrollview)

class WindowManager(ScreenManager):
    def __init__(self, **kwargs):
        super(WindowManager, self).__init__(**kwargs)
    
    def switch_to_result_screen(self, index, title, emojis, subtitle, default_title, definitions):
        root = App.get_running_app().root
        # root.ids.option_clicked.text = root.ids.result_list_main.data[index]['title']
        root.ids.specific_result_main_list.populate_page(title, emojis, subtitle, default_title, definitions)
        self.transition.direction = "left"
        self.current = "Result"
    
    def switch_to_result_screen_lemma_click(self, lemma, title, emojis, subtitle, default_title, definitions):
        root = App.get_running_app().root
        # root.ids.option_clicked.text = lemma
        root.ids.specific_result_main_list.populate_page(lemma, emojis, subtitle, default_title, definitions)
        self.transition.direction = "left"
        self.current = "Result"
    
    def switch_back_home_screen(self):
        self.transition.direction = "right"
        self.current = "Home"
    
    def switch_to_legend_screen(self):
        root = App.get_running_app().root
        root.ids.nav_drawer.set_state("close")
        self.current = "Legend"
    
    def switch_to_contact_screen(self):
        root = App.get_running_app().root
        root.ids.nav_drawer.set_state("close")
        self.current = "Contact"
    
    def switch_to_about_screen(self):
        root = App.get_running_app().root
        root.ids.nav_drawer.set_state("close")
        self.current = "About"
        


class HomeScreen(MDScreen):
    pass

class ResultScreen(MDScreen):
    pass

class LegendOfAbbrPage(MDScreen):
    pass

class ContactUsScreen(MDScreen):
    pass

class AboutScreen(MDScreen):
    pass

class ResultPageMainLayout(MDBoxLayout):
    pass

class LegendPageMainLayout(MDBoxLayout):
    pass

class ContactPageMainLayout(MDBoxLayout):
    pass

class AboutPageMainLayout(MDBoxLayout):
    pass

class ContentNavigationDrawer(MDBoxLayout):
    pass

class SoundLoadSpinner2(MDSpinner):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)

class AboutMDList(MDList):
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
        app = App.get_running_app()
        current_query = root.ids.input_word.text
        
        if not current_query:
            # Empty query
            print("Empty query")
            return
        
        ling_mode = "community"
        
        if app.linguistic_mode:
            ling_mode = "linguistic"
        
        output_res = get_main_page_results_list(current_query, ling_mode)
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
            default_title = data['lemma_wordform']['text'] if data['is_lemma'] else data['wordform_text']
            
            
            ic = data['lemma_wordform']['inflectional_category_plain_english']
            
            if app.linguistic_mode:
                ic =  data['lemma_wordform']['inflectional_category_linguistic'] 
                if ic is not None and 'linguist_info' in data['lemma_wordform'] and data['lemma_wordform']['linguist_info']['inflectional_category'] is not None:
                    ic += " (" + data['lemma_wordform']['linguist_info']['inflectional_category'] + ")"
            
            emoji = data['lemma_wordform']['wordclass_emoji']
            
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
            
            lemma_definitions = []
            if not data['is_lemma'] and data['show_form_of']:
                result_defs = data['lemma_wordform']['definitions']
                
                flag = 1
                for lemma_def in result_defs:
                    lemma_definitions.append(str(flag) + ". " + lemma_def['text'])
                    flag += 1
            
            flag = 1
                
            for definition in data['definitions']:
                defs.append(str(flag) + ". " + definition['text'])
                flag += 1
            
            if app.index_selected == 2:
                # Syllabics selected
                title = sro2syllabics(title)
                if not data['is_lemma'] and data['show_form_of']:
                    data['lemma_wordform']['text'] = sro2syllabics(data['lemma_wordform']['text'])
            elif app.index_selected == 1:
                # ēīōā selected
                title = replace_hats_to_lines_SRO(title)
                if not data['is_lemma'] and data['show_form_of']:
                    data['lemma_wordform']['text'] = replace_hats_to_lines_SRO(data['lemma_wordform']['text'])
            
            defsToPass = defs.copy()    
            
            dynamic_tile_height = 0
            for d in defsToPass:
                dynamic_tile_height += 30
                dynamic_tile_height += int(ceil(len(d) / 30)) * 35
               
            initial_result_list.append({'index': result_id_counter,
                                        'default_title': default_title,
                                        'height': dp(max(100, dynamic_tile_height)),
                                        'title': title, 
                                        'emojis': emojis, 
                                        'subtitle': subtitle,
                                        'lemma_definitions': lemma_definitions,
                                        'friendly_linguistic_breakdown_head': data['friendly_linguistic_breakdown_head'],
                                        'friendly_linguistic_breakdown_tail': data['friendly_linguistic_breakdown_tail'],
                                        'relabelled_fst_analysis': data['relabelled_fst_analysis'],
                                        'is_lemma': data['is_lemma'] if 'is_lemma' in data else True,
                                        'show_form_of': data['show_form_of'] if 'show_form_of' in data else False,
                                        'lemma_wordform': data['lemma_wordform'] if 'lemma_wordform' in data else None,
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
        app = App.get_running_app()
        self.data = data.copy()
        app.newest_result_list = data.copy()
        self.refresh_from_data()

class ResultWidget(RecycleDataViewBehavior, MDBoxLayout):
    _latest_data = None
    _rv = None
    
    index = ObjectProperty()
    default_title = ObjectProperty()
    title = ObjectProperty()
    subtitle = ObjectProperty()
    emojis = ObjectProperty()
    lemma_definitions = ObjectProperty()
    friendly_linguistic_breakdown_head = ObjectProperty()
    friendly_linguistic_breakdown_tail = ObjectProperty()
    relabelled_fst_analysis = ObjectProperty()
    is_lemma = ObjectProperty()
    show_form_of = ObjectProperty()
    lemma_wordform = ObjectProperty()
    
    # ---------------------------------------------------
    # Any new properties should be added above definitions for proper rendering
    definitions = ObjectProperty()
    
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(self.row_initialization, 0)
 
    def refresh_view_attrs(self, rv, index, data):
        self._rv = rv
        if self._latest_data is not None:
            self._latest_data["height"] = self.height
        self._latest_data = data
        super(ResultWidget, self).refresh_view_attrs(rv, index, data)
 
    def on_height(self, instance, value):
        data = self._latest_data
        if data is not None and data["height"] != value:
            data["height"] = value
            self._rv.refresh_from_data()
    
    def row_initialization(self, *args):
        if self.index != -1:
            app = App.get_running_app()
            
            title_icon_box_layout = BoxLayout()
            
            main_title_label_text_markup = "[font=bjcrus.ttf][u][color=4C0121]" + self.title + "[/color][/u][/font]"
            
            if not self.is_lemma and self.show_form_of:
                main_title_label_text_markup = "[font=bjcrus.ttf]" + self.title + "[/font]"
                
            title_label = Label(text="[font=bjcrus.ttf][u][color=4C0121]" + self.title + "[/color][/u][/font]", markup=True)
            title_label._label.refresh()
            title_label = ClickableLabel(text=main_title_label_text_markup, 
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
                                                                   user_font_size="20dp",
                                                                   pos_hint = {'center_y': 0.5}))
                
            title_icon_box_layout.add_widget(InfoTooltipButton(icon="volume-high", 
                                                                user_font_size="20dp",
                                                                on_release=self.play_sound,
                                                                pos_hint = {'center_y': 0.5}))

            self.add_widget(title_icon_box_layout)
            
            # Add the line here.
            
            if not self.is_lemma and self.show_form_of:
                
                for definition in self.definitions:
                    definition_label = MDLabel(text=definition)
                    self.add_widget(definition_label)
                
                # Add the "form of" first
                form_of_box_layout = BoxLayout()
                
                form_of = Label(text="[size=13][i]form of[/i][/size]", markup=True)
                form_of._label.refresh()
                form_of = MDLabel(text="[size=13][i]form of[/i][/size]", 
                                       markup = True,
                                       size_hint=(None, 1),
                                       width = form_of._label.texture.size[0] + 10)
                
                
                form_of_box_layout.add_widget(form_of)
                
                lemma_wordform_text = "[size=13][font=bjcrus.ttf][u][color=4C0121]" + self.lemma_wordform['text'] + "[/color][/u][/font][/size]"
                
                form_of_lemma = ClickableLabel(text=lemma_wordform_text,
                                               markup=True, 
                                               on_release=self.on_click_form_of_lemma
                                               )
                form_of_box_layout.add_widget(form_of_lemma)
                
                self.add_widget(form_of_box_layout)
                
                line_break = MDSeparator()
                self.add_widget(line_break)
                
                form_of_lemma2 = ClickableLabel(text=lemma_wordform_text,
                                               markup=True, 
                                               on_release=self.on_click_form_of_lemma
                                               )
                
                self.add_widget(form_of_lemma2)
            
            description_box_layout = BoxLayout()
            
            additional_emoji_margin = 0 if not self.emojis else 10
            
            # emoji_label = MDLabel(text="[size=14][font=NotoEmoji-Regular.ttf]" + self.emojis + "[/font][/size]", size_hint=(0.2, 1), markup=True)
            emoji_label = Label(text="[size=14][font=NotoEmoji-Regular.ttf]" + self.emojis + "[/font][/size]", markup=True)
            emoji_label._label.refresh()
            emoji_label = MDLabel(text="[size=14][font=NotoEmoji-Regular.ttf]" + self.emojis + "[/font][/size]", 
                                markup=True,
                                size_hint=(None, 1),
                                width=emoji_label._label.texture.size[0] + additional_emoji_margin)
        
            if self.subtitle == "":
                self.subtitle = "None"
        
            desc_label = MDLabel(text="[size=14]" + self.subtitle + "[/size]", markup=True)
            
            app = App.get_running_app()
            if app.display_emoji_mode == True:
                description_box_layout.add_widget(emoji_label)
            description_box_layout.add_widget(desc_label)
            
            self.add_widget(description_box_layout)
            
            definitions_to_display = self.definitions
            if not self.is_lemma and self.show_form_of:
                definitions_to_display = self.lemma_definitions
            
            for definition in definitions_to_display:
                definition_label = MDLabel(text=definition)
                self.add_widget(definition_label)
        
        else:
            root = App.get_running_app().root
            self.add_widget(MDLabel(text="[color=800000]" + "No results found for [b][i]<<" + root.ids.input_word.text + ">>" + "[/i][/b][/color]", 
                                    markup=True,
                                    halign= 'center'))
        
        self.bind(definitions = self.update_row, lemma_wordform = self.update_row)
    
    def update_row(self, *args):
        
        self.clear_widgets()
        
        if self.index == -1:
            root = App.get_running_app().root
            self.add_widget(MDLabel(text="[color=800000]" + "No results found for [b][i]<<" + root.ids.input_word.text + ">>" + "[/i][/b][/color]", 
                                    markup=True,
                                    halign= 'center'))
            return
            
        title_icon_box_layout = BoxLayout()
        
        main_title_label_text_markup = "[font=bjcrus.ttf][u][color=4C0121]" + self.title + "[/color][/u][/font]"
            
        if not self.is_lemma and self.show_form_of:
            main_title_label_text_markup = "[font=bjcrus.ttf]" + self.title + "[/font]"

        title_label = Label(text="[font=bjcrus.ttf][u][color=4C0121]" + self.title + "[/color][/u][/font]", markup=True)
        title_label._label.refresh()
        title_label = ClickableLabel(text=main_title_label_text_markup, 
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
                                                               user_font_size="20dp",
                                                               pos_hint = {'center_y': 0.5}))
            
        title_icon_box_layout.add_widget(InfoTooltipButton(icon="volume-high", 
                                                            user_font_size="20dp",
                                                            on_release=self.play_sound,
                                                            pos_hint = {'center_y': 0.5}))
        
        self.add_widget(title_icon_box_layout)
        
        if not self.is_lemma and self.show_form_of:
            for definition in self.definitions:
                definition_label = MDLabel(text=definition)
                self.add_widget(definition_label)
            
            # Add the "form of" first
            form_of_box_layout = BoxLayout()
            
            form_of = Label(text="[size=13][i]form of[/i][/size]", markup=True)
            form_of._label.refresh()
            form_of = MDLabel(text="[size=13][i]form of[/i][/size]",
                                    markup = True,
                                    size_hint=(None, 1),
                                    width = form_of._label.texture.size[0] + 10)
            
            form_of_box_layout.add_widget(form_of)
            
            lemma_wordform_text = "[size=13][font=bjcrus.ttf][u][color=4C0121]" + self.lemma_wordform['text'] + "[/color][/u][/font][/size]"
            
            app = App.get_running_app()
            
            form_of_lemma = ClickableLabel(text=lemma_wordform_text,
                                            markup=True, 
                                            on_release=self.on_click_form_of_lemma
                                            )
            
            form_of_box_layout.add_widget(form_of_lemma)
            
            self.add_widget(form_of_box_layout)
            
            line_break = MDSeparator()
            self.add_widget(line_break)
            
            form_of_lemma2 = ClickableLabel(text=lemma_wordform_text,
                                               markup=True, 
                                               on_release=self.on_click_form_of_lemma
                                               )
                
            self.add_widget(form_of_lemma2)
            
            
        
        description_box_layout = BoxLayout()
        
        additional_emoji_margin = 0 if not self.emojis else 10
        
        emoji_label = Label(text="[size=14][font=NotoEmoji-Regular.ttf]" + self.emojis + "[/font][/size]", markup=True)
        emoji_label._label.refresh()
        emoji_label = MDLabel(text="[size=14][font=NotoEmoji-Regular.ttf]" + self.emojis + "[/font][/size]", 
                              markup=True,
                              size_hint=(None, 1),
                              width=emoji_label._label.texture.size[0] + additional_emoji_margin)
        
        if self.subtitle == "":
            self.subtitle = "None"
        
        desc_label = MDLabel(text="[size=14]" + self.subtitle + "[/size]", markup=True)
        
        app = App.get_running_app()
        
        if app.display_emoji_mode == True:
            description_box_layout.add_widget(emoji_label)
        description_box_layout.add_widget(desc_label)
        
        self.add_widget(description_box_layout)
        
        # definitions_box_layout = BoxLayout(orientation="vertical")
        
        definitions_to_display = self.definitions
        if not self.is_lemma and self.show_form_of:
            definitions_to_display = self.lemma_definitions
        
        for definition in definitions_to_display:
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
        if not self.is_lemma and self.show_form_of:
            # Shouldn't be clicked/redirected.
            return
        app = App.get_running_app()
        root = App.get_running_app().root
        app.last_result_list_index_click = self.index
        root.ids.screen_manager.switch_to_result_screen(self.index, self.title, self.emojis, self.subtitle, self.default_title, self.definitions)
    
    def on_click_form_of_lemma(self, touch):
        root = App.get_running_app().root
        
        lemma = self.lemma_wordform['text']
        
        root.ids.screen_manager.switch_to_result_screen_lemma_click(lemma, self.title, self.emojis, self.subtitle, self.default_title, self.definitions)
    
    def play_sound(self, touch):
        audio_fetch_status = get_sound(self.default_title)
        
        if audio_fetch_status == 2:
            # Connection error
            toast("This feature needs a reliable internet connection.")
            return
        elif audio_fetch_status == 3:
            # No audio found
            toast("No recording available for this word.")
            return
        
        toast("Playing sound...", duration = 1)
        
        # Instead of audio URL, play the file just loaded
        sound = SoundLoader.load(SOUND_FILE_NAME)
        if sound:
            sound.play()
            
class SpecificResultMainList(MDList):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.title = None
        self.emojis = None
        self.subtitle = None
        self.default_title = None
        self.definitions = None
    
    def populate_page(self, title, emojis, subtitle, default_title, definitions):
        '''
        Populates the second result-specific page
        '''
        self.title = title
        self.emojis = emojis
        self.subtitle = subtitle
        self.default_title = default_title
        self.definitions = definitions
        
        app = App.get_running_app()
        root = App.get_running_app().root
        self.clear_widgets()
        
        if title == None and default_title == None and definitions == None:
            # This page is still empty, don't do anything!
            return
        
        details_box_layout_height = max(len(definitions) * 60, 100)
        
        top_details_box_layout = MDBoxLayout(orientation = "vertical", 
                                             padding = "20dp", 
                                             spacing = "30dp", 
                                             size_hint = (1, None),
                                             height= str(details_box_layout_height) + "dp")
        
        title_and_sound_boxlayout = BoxLayout(size_hint = (1, 0.000001))
        
        txt_main_title = app.get_syllabics_sro_correct_label(title)
        
        title_label = Label(text="[font=bjcrus.ttf][size=22]" + txt_main_title + "[/font][/size]", markup=True)
        title_label._label.refresh()
        title_label = MDLabel(text = "[font=bjcrus.ttf][size=22]" + txt_main_title + "[/size][/font]", 
                              markup=True,
                              valign = "bottom",
                              size_hint=(None, 1),
                              text_size=title_label._label.size,
                              width = title_label._label.texture.size[0] + 10,
                              height = title_label._label.texture.size[1] + 10)
        
        title_and_sound_boxlayout.add_widget(title_label)
        
        
        # Get sound playing to work
        title_and_sound_boxlayout.add_widget(InfoTooltipButton(icon="volume-high", 
                                                               user_font_size="20dp",
                                                               on_release=self.play_sound,
                                                               pos_hint={'center_y': 1}))
        
        # Add loading spinner
        title_and_sound_boxlayout.add_widget(SoundLoadSpinner2())
        
        
        top_details_box_layout.add_widget(title_and_sound_boxlayout)
        
        
        # Add description
        description_box_layout = MDBoxLayout(size_hint = (1, 0.5))
            
        additional_emoji_margin = 0 if not emojis else 10
        
        # emoji_label = MDLabel(text="[size=14][font=NotoEmoji-Regular.ttf]" + self.emojis + "[/font][/size]", size_hint=(0.2, 1), markup=True)
        emoji_label = Label(text="[size=14][font=NotoEmoji-Regular.ttf]" + emojis + "[/font][/size]", markup=True)
        emoji_label._label.refresh()
        emoji_label = MDLabel(text="[size=14][font=NotoEmoji-Regular.ttf]" + emojis + "[/font][/size]", 
                            markup=True,
                            size_hint=(None, 1),
                            width=emoji_label._label.texture.size[0] + additional_emoji_margin)
    
        desc_label = MDLabel(text="[size=14]" + subtitle + "[/size]", markup=True)
        
        if app.display_emoji_mode:
            description_box_layout.add_widget(emoji_label)
        description_box_layout.add_widget(desc_label)
        
        top_details_box_layout.add_widget(description_box_layout)
        
        # Add definitions
        for definition in definitions:
            top_details_box_layout.add_widget(MDLabel(text = definition))
        
        self.add_widget(top_details_box_layout)
        
        # Add paradigm panes
        pane_generator = paradigm_panes.PaneGenerator()
        
        pane_generator.set_layouts_dir(BASE_DIR + "/layouts")
        pane_generator.set_fst_filepath(BASE_DIR + "/core/resourcesFST/crk-strict-generator.hfstol")
        
        paradigm = pane_generator.generate_pane("amisk", "NA")
        
        paradigm_data = paradigm.copy()
        
        # Decide how many panels to add
        all_panes = []
        
        for index, pane in enumerate(paradigm_data['panes']):
            pane_header = pane['tr_rows'][0] if len(pane['tr_rows']) > 0 else None
            pane_first_row = pane['tr_rows'][1] if len(pane['tr_rows']) > 1 else {'cells': []}
            only_labels_in_first_row = True
            nlabels = 0
            
            paradigm_header = ""
            paradigm_subheader = ""
            
            if index == 0:
                paradigm_header = "Paradigms"
                paradigm_subheader = "core"
            else:
                paradigm_header = "Paradigms"
                paradigm_subheader = relabel(pane_header['label'], "english")
                
            
            for cell in pane_first_row['cells']:
                if cell['should_suppress_output']:
                    continue
                elif cell['is_label']:
                    nlabels += 1
                elif cell['is_missing'] or cell['is_empty']:
                    pass
                else:
                    only_labels_in_first_row = False
                    break
            
            if len(pane_first_row['cells']) == 0:
                only_labels_in_first_row = False
            
            if not only_labels_in_first_row:
                print("Adding pane directly!")
                all_panes.append({'pane': pane, 'header': paradigm_header, 'subheader': paradigm_subheader})
            else:
                # We need to separately add the pane.
                print("Need to divide pane - nlabels columns: ", nlabels)
                for i in range(1, nlabels + 1):
                    current_columns = [0, i]
                    altered_pane = {'tr_rows': []}
                    for i1, row in enumerate(pane['tr_rows']):
                        if row['is_header']:
                            paradigm_header = relabel(row['label'], "english")
                            altered_pane['tr_rows'].append(row)
                        else:
                            cells_dict = row.copy()
                            cells_dict['cells'] = []
                            # The subheaders are not right in all paradigm panes subheaders
                            for idx, cell in enumerate(row['cells']):
                                if idx in current_columns:
                                    cells_dict['cells'].append(cell)
                                    if i1 == 1 and idx == current_columns[1] and cell["is_label"]:
                                        paradigm_subheader = relabel(cell["label"], "english")
                            altered_pane['tr_rows'].append(cells_dict)
                    all_panes.append({'pane': altered_pane, 'header': paradigm_header, 'subheader': paradigm_subheader})
            
            print("=" * 80)
            
        for each_pane in all_panes:
            self.add_widget(MDExpansionPanel(
                            icon="bookshelf",
                            content=ParadigmLabelContent(each_pane['pane']),
                            panel_cls=MDExpansionPanelTwoLine(
                                text= each_pane['header'],
                                secondary_text= each_pane['subheader']
                            ),
                            ))
        
        # pane_1 = MDExpansionPanel(
        #             icon="bookshelf",
        #             content=ParadigmLabelContent(paradigm_data),
        #             panel_cls=MDExpansionPanelTwoLine(
        #                 text= 'Paradigms',
        #                 secondary_text= 'Click to expand'
        #             ),
        #         )
        
        # self.add_widget(pane_1)
        
    def play_sound(self, *args):
        print("Default title: ", self.default_title)
        app = App.get_running_app()
        app.spinner2_active = True
        audio_fetch_status = get_sound(self.default_title)
        
        if audio_fetch_status == 2:
            # Connection error
            app.spinner2_active = False
            toast("This feature needs a reliable internet connection.")
            return
        elif audio_fetch_status == 3:
            # No audio found
            app.spinner2_active = False
            toast("No recording available for this word.")
            return
        
        # Instead of audio URL, play the file just loaded
        sound = SoundLoader.load(SOUND_FILE_NAME)
        if sound:
            print("Playing sound...")
            sound.on_stop = self.stop_loader
            sound.play()
        
    def stop_loader(self):
        print("Sound stopped")
        app = App.get_running_app()
        app.spinner2_active = False
        

class MorphodictApp(MDApp):
    legend_of_abbr_text = LEGEND_OF_ABBREVIATIONS_TEXT
    contact_us_text = CONTACT_US_TEXT
    about_text_source_material = ABOUT_TEXT_SOURCE_MATERIALS
    about_text_credit = ABOUT_TEXT_CREDITS
    spinner2_active = BooleanProperty(defaultvalue = False)
    # result_default_size = NumericProperty(defaultvalue = dp(200))
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.menu = None
        self.index_selected = 0
        self.index_selected_paradigms = 0
        self.paradigm_labels_menu = None
        self.linguistic_mode = False
        self.display_emoji_mode = False
        self.last_result_list_index_click = None
        self.newest_result_list = []
    
    def build(self):
        # self.theme_cls.theme_style = "Dark"  # "Light" - comment this on for dark theme.
        Window.clearcolor = (0.933, 1, 0.92, 1)
        
        # Label Settings Menu
        label_settings_items = [{'index': 0, 
                                 'text': "SRO(êîôâ)", 
                                 "viewclass": "LabelSettingsItem", 
                                 "on_release": lambda x=f"SRO(êîôâ)": self.set_item(x),
                                 "text_color": (0.543, 0, 0, 1)},
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
        
        paradigm_settings_items = [{'index': 0, 
                                 'text': "Plain English Labels", 
                                 "viewclass": "LabelSettingsItem", 
                                 "on_release": lambda x=f"Plain English Labels": self.set_item_paradigm(x),
                                 "text_color": (0.543, 0, 0, 1)},
                                {'index': 1, 'text': "Linguistic labels", 
                                 "viewclass": "LabelSettingsItem", 
                                 "on_release": lambda x=f"Linguistic labels": self.set_item_paradigm(x),
                                 "text_color": (0, 0, 0, 1)},
                                {'index': 2, 
                                 'text': "nêhiyawêwin labels", 
                                 "viewclass": "LabelSettingsItem", 
                                 "on_release": lambda x=f"nêhiyawêwin labels": self.set_item_paradigm(x),
                                 "text_color": (0, 0, 0, 1)}]
        
        self.paradigm_labels_menu = MDDropdownMenu(
            caller=self.root.ids.paradigm_label_settings_dropdown,
            items=paradigm_settings_items,
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
            label_settings_items[2]["text_color"] = (0.543, 0, 0, 1)
            self.index_selected = 2
        elif text_item == "SRO(ēīōā)":
            label_settings_items[1]["text_color"] = (0.543, 0, 0, 1)
            self.index_selected = 1
        else:
            label_settings_items[0]["text_color"] = (0.543, 0, 0, 1)
            self.index_selected = 0
        
        self.menu.items = label_settings_items
        self.root.ids.label_settings_dropdown.set_item(text_item)
        self.root.ids.main_box_layout.on_submit_word()
        second_page_population_list = self.root.ids.specific_result_main_list
        self.root.ids.specific_result_main_list.populate_page(second_page_population_list.title,
                                                              second_page_population_list.emojis, 
                                                              second_page_population_list.subtitle,
                                                              second_page_population_list.default_title,
                                                              second_page_population_list.definitions)
        self.menu.dismiss()
    
    def set_item_paradigm(self, text_item):
        if self.root.ids.paradigm_label_settings_dropdown.current_item == text_item:
            # Same option chosen, don't do anything
            return
        
        paradigm_settings_items = [{'index': 0, 
                                 'text': "Plain English Labels", 
                                 "viewclass": "LabelSettingsItem", 
                                 "on_release": lambda x=f"Plain English Labels": self.set_item_paradigm(x),
                                 "text_color": (0, 0, 0, 1)},
                                {'index': 1, 'text': "Linguistic labels", 
                                 "viewclass": "LabelSettingsItem", 
                                 "on_release": lambda x=f"Linguistic labels": self.set_item_paradigm(x),
                                 "text_color": (0, 0, 0, 1)},
                                {'index': 2, 
                                 'text': "nêhiyawêwin labels", 
                                 "viewclass": "LabelSettingsItem", 
                                 "on_release": lambda x=f"nêhiyawêwin labels": self.set_item_paradigm(x),
                                 "text_color": (0, 0, 0, 1)}]
        
        if text_item == "nêhiyawêwin labels":
            paradigm_settings_items[2]["text_color"] = (0.543, 0, 0, 1)
            self.index_selected_paradigms = 2
        elif text_item == "Linguistic labels":
            paradigm_settings_items[1]["text_color"] = (0.543, 0, 0, 1)
            self.index_selected_paradigms = 1
        else:
            paradigm_settings_items[0]["text_color"] = (0.543, 0, 0, 1)
            self.index_selected_paradigms = 0
        
        self.paradigm_labels_menu.items = paradigm_settings_items
        self.root.ids.paradigm_label_settings_dropdown.set_item(text_item)
        
        # Make additional callbacks here
        second_page_population_list = self.root.ids.specific_result_main_list
        self.root.ids.specific_result_main_list.populate_page(second_page_population_list.title,
                                                              second_page_population_list.emojis, 
                                                              second_page_population_list.subtitle,
                                                              second_page_population_list.default_title,
                                                              second_page_population_list.definitions)
        
        
        self.paradigm_labels_menu.dismiss()
    
    
    def on_start(self):
        # Preload these things
        def on_release_help(arg):
            webbrowser.open("https://altlab.ualberta.ca/itwewina/#help")
            
        def on_release_settings(arg):
            print("Settings pressed!")
            
        def on_release_legend(arg):
            root = App.get_running_app().root
            root.ids.screen_manager.switch_to_legend_screen()
        
        def on_release_contact_us(arg):
            root = App.get_running_app().root
            root.ids.screen_manager.switch_to_contact_screen()
        
        def on_release_about(arg):
            root = App.get_running_app().root
            root.ids.screen_manager.switch_to_about_screen()
            
        
        drawer_items_list = [{'text': 'Help', 'icon': "help-circle", 'callback': on_release_help},
                             {'text': 'Legend of Abbreviations', 'icon': 'text-box-outline', 'callback': on_release_legend},
                             {'text': 'About', 'icon': "account-group", 'callback': on_release_about},
                             {'text': 'Contact us', 'icon': "email", 'callback': on_release_contact_us},
                             # {'text': 'Settings', 'icon': "cog", 'callback': on_release_settings}
                            ]
        
        for drawer_item in drawer_items_list:
            row_item = OneLineIconListItem(text=drawer_item['text'], on_release=drawer_item['callback'])
            row_item.add_widget(IconLeftWidget(icon=drawer_item['icon']))
            self.root.ids.navigation_drawer_list.add_widget(row_item)
        return super().on_start()

    def on_legend_ref_press(self, instance, ref):
        root = App.get_running_app().root
        root.ids.input_word.text = ref
        root.ids.main_box_layout.on_submit_word()
        root.ids.screen_manager.switch_back_home_screen()
    
    def on_contact_ref_press(self, instance, ref):
        webbrowser.open(HELP_CONTACT_FORM_LINK)
        
    def on_about_ref_press(self, instance, ref):
        about_url_links = {
            "about-1": "https://uofrpress.ca/Books/C/Cree-Words",
            "about-2": "https://altlab.ualberta.ca/wp-content/uploads/2019/01/Snoek_et_al_CEL1_2014.pdf",
            "about-3": "https://altlab.ualberta.ca/wp-content/uploads/2019/01/Harrigan_Schmirler_Arppe_Antonsen_Trosterud_Wolvengrey_2017fc.pdf",
            "about-4": "https://uofrpress.ca/Books/C/Cree-Words",
            "about-5": "https://www.altlab.dev/maskwacis/dictionary.html",
            "about-6": "https://www.altlab.dev/maskwacis/",
            "about-7": "https://www.maskwacised.ca",
            "about-8": "https://altlab.ualberta.ca",
            "about-9": "https://www.altlab.dev/maskwacis/Speakers/speakers.html",
            "about-10": "https://github.com/UAlbertaALTLab/morphodict",
            "about-11": "https://github.com/UAlbertaALTLab/morphodict/blob/main/AUTHORS.md",
            "about-12": "https://nrc.canada.ca/en/research-development/research-collaboration/programs/canadian-indigenous-languages-technology-project",
            "about-13": "https://nrc.canada.ca/en"
        }
        
        webbrowser.open(about_url_links[ref])
    
    def get_syllabics_sro_correct_label(self, string: str) -> str:
        if self.index_selected == 2:
            # Syllabics
            string = sro2syllabics(string)
        elif self.index_selected == 1:
            # ēīōā selected
            string = replace_hats_to_lines_SRO(string)
        
        return string

if __name__ == '__main__':
    MorphodictApp().run()
