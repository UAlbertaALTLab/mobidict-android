__version__ = "1.0.0"
from math import ceil
from functools import partial
import webbrowser
import threading
import paradigm_panes
import os
import time

from kivy.properties import ObjectProperty
from kivy.clock import Clock, mainthread
from kivy.app import App
from kivy.metrics import dp
from kivy.properties import StringProperty, BooleanProperty, NumericProperty
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.screenmanager import ScreenManager
from kivy.uix.button import ButtonBehavior
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.core.audio import SoundLoader
from kivy.storage.jsonstore import JsonStore

from kivymd.app import MDApp

from kivymd.uix.list import MDList, OneLineListItem, OneLineIconListItem, IconLeftWidget
from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard, MDSeparator
from kivymd.uix.tooltip import MDTooltip
from kivymd.uix.button import MDIconButton
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.spinner import MDSpinner
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.toast import toast
from kivymd.uix.expansionpanel import MDExpansionPanel, MDExpansionPanelTwoLine

from cree_sro_syllabics import sro2syllabics

from backend import get_main_page_results_list
from api.api import get_sound
from general import SOUND_FILE_NAME, LEGEND_OF_ABBREVIATIONS_TEXT, CONTACT_US_TEXT, HELP_CONTACT_FORM_LINK, ABOUT_TEXT_SOURCE_MATERIALS, ABOUT_TEXT_CREDITS, cells_contains_only_column_labels, is_core_column_header
from core.frontend.relabelling import relabel, relabel_source, relabel_plain_english, relabel_linguistic_long

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

class ParadigmExpansionPanel(MDExpansionPanel):
    def __init__(self, is_first, dynamic_height, **kwargs ):
        super().__init__(**kwargs)
        self.is_first = is_first
        self.dynamic_height = dynamic_height
        Clock.schedule_once(self.panel_op, 0)
    def panel_op(self, args):
        if self.is_first:
            # self.check_open_panel(self)
            self.height += self.dynamic_height
            self.open_panel()
        


class EmojiSwitch(MDCheckbox):
    def change_mode(self, current_query, ling_mode):
        app = App.get_running_app()
        output_result_list = get_main_page_results_list(current_query, ling_mode)
        Clock.schedule_once(partial(self.update_emoji_ui, output_result_list))
        time.sleep(1)
    
    def update_emoji_ui(self, prefetched_list, *args):
        app = App.get_running_app()
        store = JsonStore('store.json')
        if self.active:
            app.display_emoji_mode = True
            store.put('display_emoji_mode', display_emoji_mode = True)
        else:
            app.display_emoji_mode = False
            store.put('display_emoji_mode', display_emoji_mode = False)
        
        app.root.ids.main_box_layout.on_submit_word(prefetched_result_list=prefetched_list)
        second_page_population_list = app.root.ids.specific_result_main_list
        app.root.ids.specific_result_main_list.populate_page( second_page_population_list.title,
                                                              second_page_population_list.emojis,
                                                              app.newest_result_list[app.last_result_list_index_click]['subtitle'] if app.last_result_list_index_click is not None else "",
                                                              second_page_population_list.default_title,
                                                              second_page_population_list.inflectional_category,
                                                              second_page_population_list.paradigm_type,
                                                              second_page_population_list.lemma_paradigm_type,
                                                              second_page_population_list.definitions)
        app.main_loader_spinner_toggle()

    def emoji_display_thread(self):
        app = App.get_running_app()
        app.main_loader_spinner_toggle()

        current_query = app.root.ids.input_word.text
        
        ling_mode = "community"
        
        if app.index_selected_paradigms == 1:
            ling_mode = "linguistic"
        elif app.index_selected_paradigms == 2:
            ling_mode = "source_language"

        # https://docs.python.org/3/library/multiprocessing.html - use this!
        threading.Thread(target=(self.change_mode), args=[current_query, ling_mode]).start()

class InflectionalSwitch(MDCheckbox):
    def change_mode(self):
        app = App.get_running_app()
        store = JsonStore('store.json')
        if self.active:
            app.display_inflectional_category = True
            store.put('display_inflectional_category', display_inflectional_category = True)
        else:
            app.display_inflectional_category = False
            store.put('display_inflectional_category', display_inflectional_category = False)
        
        app.root.ids.main_box_layout.on_submit_word()
        second_page_population_list = app.root.ids.specific_result_main_list
        app.root.ids.specific_result_main_list.populate_page( second_page_population_list.title,
                                                              second_page_population_list.emojis, 
                                                              app.newest_result_list[app.last_result_list_index_click]['subtitle'] if app.last_result_list_index_click is not None else "",
                                                              second_page_population_list.default_title,
                                                              second_page_population_list.inflectional_category,
                                                              second_page_population_list.paradigm_type,
                                                              second_page_population_list.lemma_paradigm_type,
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
    
    def switch_to_result_screen(self, index, title, emojis, subtitle, default_title, inflectional_category, paradigm_type, definitions):
        root = App.get_running_app().root
        # root.ids.option_clicked.text = root.ids.result_list_main.data[index]['title']
        root.ids.specific_result_main_list.populate_page(title, emojis, subtitle, default_title, inflectional_category, paradigm_type, None, definitions)
        self.transition.direction = "left"
        self.current = "Result"
    
    def switch_to_result_screen_lemma_click(self, lemma, title, emojis, subtitle, default_title, inflectional_category, paradigm_type, lemma_paradigm_type, definitions):
        root = App.get_running_app().root
        # root.ids.option_clicked.text = lemma
        root.ids.specific_result_main_list.populate_page(lemma, emojis, subtitle, default_title, inflectional_category, paradigm_type, lemma_paradigm_type, definitions)
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

class MainLoaderSpinner(MDSpinner):
    pass

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
    def on_submit_word(self, widget= None, prefetched_result_list = None):
        root = App.get_running_app().root
        app = App.get_running_app()
        
        store = JsonStore('store.json')
        
        current_query = root.ids.input_word.text
        
        if not current_query:
            # Empty query
            print("Empty query")
            return
        
        ling_mode = "community"
        
        if app.index_selected_paradigms == 1:
            ling_mode = "linguistic"
        elif app.index_selected_paradigms == 2:
            ling_mode = "source_language"
        
        output_res = prefetched_result_list

        if prefetched_result_list is None:
            output_res = get_main_page_results_list(current_query, ling_mode)
        
        resultToPrint = output_res.copy()
        self.display_result_list(resultToPrint)
    
    def display_result_list(self, data_list):
        result_list_view = MDList()
        initial_result_list = []
        
        result_id_counter = 0
        
        app = App.get_running_app()
        
        for data in data_list:
            title = data['lemma_wordform']['text'] if data['is_lemma'] else data['wordform_text']
            default_title = data['lemma_wordform']['text'] if data['is_lemma'] else data['wordform_text']
            
            paradigm_type = data['lemma_wordform']['paradigm'] if data['is_lemma'] else None
            lemma_paradigm_type = None
            
            # Note that the ic can also be set using relabel_plain_english and relabel_linguistic_long
            
            inflectional_category = data['lemma_wordform']['inflectional_category'] if data['is_lemma'] or (not data['is_lemma'] and data['show_form_of']) else "None"
            ic = data['lemma_wordform']['inflectional_category_plain_english']
            
            if app.index_selected_paradigms == 1:
                ic =  data['lemma_wordform']['inflectional_category_linguistic'] 
                if ic is not None and 'linguist_info' in data['lemma_wordform'] and data['lemma_wordform']['linguist_info']['inflectional_category'] is not None:
                    ic += " (" + data['lemma_wordform']['linguist_info']['inflectional_category'] + ")"
            
            if app.index_selected_paradigms == 2 and inflectional_category != "None":
                ic = relabel_source(inflectional_category)
            
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
            
            default_title_lemma = data['lemma_wordform']['text']
            
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
            
            if not data['is_lemma'] and data['show_form_of']:
                lemma_paradigm_type = data['lemma_wordform']['paradigm']
                dynamic_tile_height += 15
                for d in lemma_definitions:
                    dynamic_tile_height += 30
                    dynamic_tile_height += int(ceil(len(d) / 30)) * 35
            
            # If linguistic mode, increase dynamic height to give space for the larger subtitle
            if app.index_selected_paradigms == 1 or app.index_selected_paradigms == 2:
                dynamic_tile_height += 20
            
               
            initial_result_list.append({'index': result_id_counter,
                                        'default_title': default_title,
                                        'height': dp(max(100, dynamic_tile_height)),
                                        'title': title, 
                                        'emojis': emojis, 
                                        'subtitle': subtitle,
                                        'inflectional_category': inflectional_category,
                                        'paradigm_type': paradigm_type,
                                        'lemma_paradigm_type': lemma_paradigm_type,
                                        'lemma_definitions': lemma_definitions,
                                        'friendly_linguistic_breakdown_head': data['friendly_linguistic_breakdown_head'],
                                        'friendly_linguistic_breakdown_tail': data['friendly_linguistic_breakdown_tail'],
                                        'relabelled_fst_analysis': data['relabelled_fst_analysis'],
                                        'is_lemma': data['is_lemma'] if 'is_lemma' in data else True,
                                        'show_form_of': data['show_form_of'] if 'show_form_of' in data else False,
                                        'default_title_lemma': default_title_lemma,
                                        'lemma_wordform': data['lemma_wordform'] if 'lemma_wordform' in data else None,
                                        'definitions': defsToPass
                                        })
            
            result_id_counter += 1
        
        if len(initial_result_list) == 0:
            root = App.get_running_app().root
            initial_result_list.append({'index': -1, 'title': 'No results found!', 'definitions': [root.ids.input_word.text]})
        
        root = App.get_running_app().root
        
        root.ids.result_list_main.update_data(initial_result_list)

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
    inflectional_category = ObjectProperty()
    paradigm_type = ObjectProperty(allownone = True)
    lemma_paradigm_type = ObjectProperty(allownone = True)
    lemma_definitions = ObjectProperty()
    friendly_linguistic_breakdown_head = ObjectProperty()
    friendly_linguistic_breakdown_tail = ObjectProperty()
    relabelled_fst_analysis = ObjectProperty()
    is_lemma = ObjectProperty()
    show_form_of = ObjectProperty()
    default_title_lemma = ObjectProperty()
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
            
            main_title_label_text_markup = "[font=bjcrus.ttf][color=4C0121][size=20dp][u]" + self.title + "[/u][/size][/color][/font]"
            
            if not self.is_lemma and self.show_form_of:
                main_title_label_text_markup = "[font=bjcrus.ttf]" + self.title + "[/font]"
                
            title_label = Label(text="[font=bjcrus.ttf][color=4C0121][size=20dp][u]" + self.title + "[/u][/size][/color][/font]", markup=True)
            title_label._label.refresh()

            title_label_width = title_label._label.texture.size[0] + 10
            title_label = ClickableLabel(text=main_title_label_text_markup, 
                                            markup=True,
                                            on_release=self.on_click_label,
                                            size_hint=(None, 1),
                                            width = title_label._label.texture.size[0] + 10)

            title_icon_box_layout.add_widget(title_label)
            
            tooltip_and_sound_float_layout = FloatLayout(size=(150, 150))
            
            if self.friendly_linguistic_breakdown_head or self.friendly_linguistic_breakdown_tail:
                tooltip_content = ""
                
                for chunk in self.relabelled_fst_analysis:
                    chunk_label = chunk['label']
                    if len(chunk_label) > 0:
                        chunk_label = chunk_label.replace("→", "->")
                    tooltip_content += chunk_label + "\n"
                
                if len(tooltip_content) > 0:
                    tooltip_content = tooltip_content[:-1]
                
                tooltip_and_sound_float_layout.add_widget(InfoTooltipButton(icon="information",
                                                                   tooltip_text= tooltip_content,
                                                                   icon_size="19dp",
                                                                   shift_y="100dp",
                                                                   size_hint_x = 0.5,
                                                                   pos_hint = {'center_y': 0.5},
                                                                   pos=(app.root.ids.input_word.pos[0] + title_label_width, title_label_width)))
                
            tooltip_and_sound_float_layout.add_widget(InfoTooltipButton(icon="volume-high", 
                                                                icon_size="19dp",
                                                                on_release=self.play_sound,
                                                                size_hint_x = 0.5,
                                                                pos_hint = {'center_y': 0.5},
                                                                pos=(app.root.ids.input_word.pos[0] + title_label_width + 60, title_label_width + 60)))

            title_icon_box_layout.add_widget(tooltip_and_sound_float_layout)
            self.add_widget(title_icon_box_layout)
            
            # Add the line here.
            
            if not self.is_lemma and self.show_form_of:
                
                for definition in self.definitions:
                    definition_label = MDLabel(text=definition)
                    self.add_widget(definition_label)
                
                # Add the "form of" first
                form_of_box_layout = BoxLayout()
                
                form_of = Label(text="[size=14dp][i]form of[/i][/size]", markup=True)
                form_of._label.refresh()
                form_of = MDLabel(text="[size=14dp][i]form of[/i][/size]", 
                                       markup = True,
                                       size_hint=(None, 1),
                                       width = form_of._label.texture.size[0] + 10)
                
                
                form_of_box_layout.add_widget(form_of)
                
                lemma_wordform_text = "[size=14dp][font=bjcrus.ttf][u][color=4C0121]" + self.lemma_wordform['text'] + "[/color][/u][/font][/size]"
                
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
            
            app = App.get_running_app()
            
            # Add the inflectional category only if the option is on
            
            if app.display_inflectional_category:
                inflection_label = Label(text="[size=15dp]" + self.inflectional_category + "[/size]", markup=True)
                inflection_label._label.refresh()
                inflection_label = MDLabel(text="[size=15dp]" + self.inflectional_category + "[/size]", 
                                    markup=True,
                                    size_hint=(None, 1),
                                    width=inflection_label._label.texture.size[0] + 5)
                
                description_box_layout.add_widget(inflection_label)
            
            
            additional_emoji_margin = 0 if not self.emojis else 10
            
            emoji_label = Label(text="[size=15dp][font=NotoEmoji-Regular.ttf]" + self.emojis + "[/font][/size]", markup=True)
            emoji_label._label.refresh()
            emoji_label = MDLabel(text="[size=15dp][font=NotoEmoji-Regular.ttf]" + self.emojis + "[/font][/size]", 
                                markup=True,
                                size_hint=(None, 1),
                                width=emoji_label._label.texture.size[0] + additional_emoji_margin)
        
            if self.subtitle == "":
                self.subtitle = "None"
        
            desc_label = MDLabel(text="[size=15dp]" + self.subtitle + "[/size]", markup=True)
            
            
            if app.display_emoji_mode == True:
                description_box_layout.add_widget(emoji_label)
            description_box_layout.add_widget(desc_label)
            
            self.add_widget(description_box_layout)
            
            definitions_to_display = self.definitions
            if not self.is_lemma and self.show_form_of:
                definitions_to_display = self.lemma_definitions
            
            for definition in definitions_to_display:
                definition_label = MDLabel(text="[size=14dp]" + definition + "[/size]", markup = True)
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
        
        main_title_label_text_markup = "[font=bjcrus.ttf][u][color=4C0121][size=20dp]" + self.title + "[/size][/color][/u][/font]"
            
        if not self.is_lemma and self.show_form_of:
            main_title_label_text_markup = "[font=bjcrus.ttf]" + self.title + "[/font]"

        title_label = Label(text="[font=bjcrus.ttf][u][color=4C0121][size=20dp]" + self.title + "[/size][/color][/u][/font]", markup=True)
        title_label._label.refresh()
        
        title_label_width = title_label._label.texture.size[0] + 10
        
        title_label = ClickableLabel(text=main_title_label_text_markup, 
                                        markup=True,
                                        on_release=self.on_click_label,
                                        size_hint=(None, 1),
                                        width = title_label._label.texture.size[0] + 10)

        title_icon_box_layout.add_widget(title_label)
        
        tooltip_and_sound_float_layout = FloatLayout(size=(150, 150))
        
        app = App.get_running_app()
        
        if self.friendly_linguistic_breakdown_head or self.friendly_linguistic_breakdown_tail:
            tooltip_content = ""
            for chunk in self.relabelled_fst_analysis:
                chunk_label = chunk['label']
                if len(chunk_label) > 0:
                    chunk_label = chunk_label.replace("→", "->")
                tooltip_content += chunk_label + "\n"
            
            if len(tooltip_content) > 0:
                tooltip_content = tooltip_content[:-1]
                
            tooltip_and_sound_float_layout.add_widget(InfoTooltipButton(icon="information", 
                                                               tooltip_text= tooltip_content,
                                                               shift_y="100dp",
                                                               icon_size="19dp",
                                                               size_hint_x = 0.5,
                                                               pos_hint = {'center_y': 0.5},
                                                               pos = (app.root.ids.input_word.pos[0] + title_label_width, title_label_width)))
            
        tooltip_and_sound_float_layout.add_widget(InfoTooltipButton(icon="volume-high", 
                                                            icon_size="19dp",
                                                            on_release=self.play_sound,
                                                            size_hint_x = 0.5,
                                                            pos_hint = {'center_y': 0.5},
                                                            pos = (app.root.ids.input_word.pos[0] + title_label_width + 60, title_label_width)))
        
        title_icon_box_layout.add_widget(tooltip_and_sound_float_layout)
        self.add_widget(title_icon_box_layout)
        
        if not self.is_lemma and self.show_form_of:
            for definition in self.definitions:
                definition_label = MDLabel(text=definition)
                self.add_widget(definition_label)
            
            # Add the "form of" first
            form_of_box_layout = BoxLayout()
            
            form_of = Label(text="[size=14dp][i]form of[/i][/size]", markup=True)
            form_of._label.refresh()
            form_of = MDLabel(text="[size=14dp][i]form of[/i][/size]",
                                    markup = True,
                                    size_hint=(None, 1),
                                    width = form_of._label.texture.size[0] + 10)
            
            form_of_box_layout.add_widget(form_of)
            
            lemma_wordform_text = "[size=14dp][font=bjcrus.ttf][u][color=4C0121]" + self.lemma_wordform['text'] + "[/color][/u][/font][/size]"
            
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
        
        app = App.get_running_app()
        
        # Add the inflectional category
        if app.display_inflectional_category:
            inflection_label = Label(text="[size=15dp]" + self.inflectional_category + "[/size]", markup=True)
            inflection_label._label.refresh()
            inflection_label = MDLabel(text="[size=15dp]" + self.inflectional_category + "[/size]", 
                                markup=True,
                                size_hint=(None, 1),
                                width=inflection_label._label.texture.size[0] + 5)
            
            description_box_layout.add_widget(inflection_label)
            
        additional_emoji_margin = 0 if not self.emojis else 10
        
        emoji_label = Label(text="[size=15dp][font=NotoEmoji-Regular.ttf]" + self.emojis + "[/font][/size]", markup=True)
        emoji_label._label.refresh()
        emoji_label = MDLabel(text="[size=15dp][font=NotoEmoji-Regular.ttf]" + self.emojis + "[/font][/size]", 
                              markup=True,
                              size_hint=(None, 1),
                              width=emoji_label._label.texture.size[0] + additional_emoji_margin)
        
        if self.subtitle == "":
            self.subtitle = "None"
        
        desc_label = MDLabel(text="[size=15dp]" + self.subtitle + "[/size]", markup=True)
        
        if app.display_emoji_mode == True:
            description_box_layout.add_widget(emoji_label)
        description_box_layout.add_widget(desc_label)
        
        self.add_widget(description_box_layout)
        
        # definitions_box_layout = BoxLayout(orientation="vertical")
        
        definitions_to_display = self.definitions
        if not self.is_lemma and self.show_form_of:
            definitions_to_display = self.lemma_definitions
        
        for definition in definitions_to_display:
            definition_label = MDLabel(text="[size=14dp]" + definition + "[/size]", markup = True)
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
        root.ids.screen_manager.switch_to_result_screen(self.index, self.title, self.emojis, self.subtitle, self.default_title, self.inflectional_category, self.paradigm_type, self.definitions)
    
    def on_click_form_of_lemma(self, touch):
        root = App.get_running_app().root
        
        lemma = self.lemma_wordform['text']
        
        root.ids.screen_manager.switch_to_result_screen_lemma_click(lemma, self.title, self.emojis, self.subtitle, self.default_title_lemma, self.inflectional_category, self.paradigm_type, self.lemma_paradigm_type, self.definitions)
    
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
        elif audio_fetch_status == 4:
            # No audio found
            toast("Audio currently unavailable.")
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
        self.inflectional_category = None
        self.paradigm_type = None
        self.lemma_paradigm_type = None
        self.definitions = None
    
    def populate_page(self, title, emojis, subtitle, default_title, inflectional_category, paradigm_type, lemma_paradigm_type, definitions):
        '''
        Populates the second result-specific page
        '''
        self.title = title
        self.emojis = emojis
        self.subtitle = subtitle
        self.default_title = default_title
        self.inflectional_category = inflectional_category
        self.paradigm_type = paradigm_type
        self.lemma_paradigm_type = lemma_paradigm_type
        self.definitions = definitions
        
        app = App.get_running_app()
        root = App.get_running_app().root
        self.clear_widgets()
        
        if title is None and default_title is None and definitions is None:
            # This page is still empty, don't do anything!
            return
        
        dynamic_details_height = 0
        
        for d in definitions:
            dynamic_details_height += max(int(ceil(len(d) / 30)) * 40, 60)
        
        details_box_layout_height = max(dynamic_details_height, 100)
        
        top_details_box_layout = MDBoxLayout(orientation = "vertical", 
                                             padding = "20dp", 
                                             spacing = "30dp", 
                                             size_hint = (1, None),
                                             height= str(details_box_layout_height) + "dp")
        
        title_and_sound_boxlayout = BoxLayout(size_hint = (1, 0.000001))
        
        txt_main_title = app.get_syllabics_sro_correct_label(title)
        
        title_label = Label(text="[font=bjcrus.ttf][size=28]" + txt_main_title + "[/font][/size]", markup=True)
        title_label._label.refresh()
        title_label = MDLabel(text = "[font=bjcrus.ttf][size=28]" + txt_main_title + "[/size][/font]", 
                              markup=True,
                              valign = "bottom",
                              size_hint=(None, 1),
                              text_size=title_label._label.size,
                              width = title_label._label.texture.size[0] + 10,
                              height = title_label._label.texture.size[1] + 10)
        
        title_and_sound_boxlayout.add_widget(title_label)
        
        
        # Get sound playing to work
        title_and_sound_boxlayout.add_widget(InfoTooltipButton(icon="volume-high", 
                                                               icon_size="19dp",
                                                               on_release=self.play_sound,
                                                               pos_hint={'center_y': 1}))
        
        # Add loading spinner
        title_and_sound_boxlayout.add_widget(SoundLoadSpinner2())
        
        
        top_details_box_layout.add_widget(title_and_sound_boxlayout)
        
        
        # Add description
        description_box_layout = MDBoxLayout(size_hint = (1, 0.5))
        
        # Add the inflectional category
        if app.display_inflectional_category:
            inflection_label = Label(text="[size=24]" + self.inflectional_category + "[/size]", markup=True)
            inflection_label._label.refresh()
            inflection_label = MDLabel(text="[size=24]" + self.inflectional_category + "[/size]", 
                                markup=True,
                                size_hint=(None, 1),
                                width=inflection_label._label.texture.size[0] + 5)
            
            description_box_layout.add_widget(inflection_label)
            
        additional_emoji_margin = 0 if not emojis else 10
        
        # emoji_label = MDLabel(text="[size=14][font=NotoEmoji-Regular.ttf]" + self.emojis + "[/font][/size]", size_hint=(0.2, 1), markup=True)
        emoji_label = Label(text="[size=24][font=NotoEmoji-Regular.ttf]" + emojis + "[/font][/size]", markup=True)
        emoji_label._label.refresh()
        emoji_label = MDLabel(text="[size=24][font=NotoEmoji-Regular.ttf]" + emojis + "[/font][/size]", 
                            markup=True,
                            size_hint=(None, 1),
                            width=emoji_label._label.texture.size[0] + additional_emoji_margin)
    
        desc_label = MDLabel(text="[size=24]" + subtitle + "[/size]", markup=True)
        
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
        
        paradigm = {'panes': []}
        
        if lemma_paradigm_type is None:
            if paradigm_type is not None and paradigm_type in app.paradigm_pane_layouts_available:
                paradigm = pane_generator.generate_pane(default_title, paradigm_type)
            elif paradigm_type is None:
                print("Paradigm Type (currently unavailable): ", paradigm_type)
                return
        elif lemma_paradigm_type in app.paradigm_pane_layouts_available:
            paradigm = pane_generator.generate_pane(default_title, lemma_paradigm_type)
        else:
            print("Paradigm Type (currently unavailable): ", paradigm_type)
            return
        
        paradigm_data = paradigm.copy()
        
        # Decide how many panels to add
        all_panes = []
        header, subheader = None, None
        
        for pane_idx, pane in enumerate(paradigm_data['panes']):
            is_core_pane = False
            is_next_row_after_labels = False
            current_num_cols = 0
            current_panes = []
            for row_idx, tr_row in enumerate(pane['tr_rows']):
                print("[Test] current row: ", tr_row)
                if not tr_row['is_header']:
                    
                    # Check if the pane is a Core pane
                    if not is_core_pane and cells_contains_only_column_labels(tr_row['cells'])[0] and is_core_column_header(tr_row['cells']):
                        header = "Core"
                        is_core_pane = True
                        continue
                    
                    # Check if a row contains only column labels
                    is_row_only_col_labels, num_cols = cells_contains_only_column_labels(tr_row['cells'])
                    if is_row_only_col_labels:
                        current_num_cols = num_cols
                        is_next_row_after_labels = True
                        for cell_idx, cell in enumerate(tr_row['cells']):
                            # Check if it's not the first cell of the cells
                            # as that's usually empty!
                            if cell_idx != 0:
                                current_panes.append({'tr_rows': []})
                        continue
                    
                    print("Current panes: every iteration", current_panes)
                    current_row = tr_row.copy()
                    current_row['cells'] = []
                    for cell_idx, cell in enumerate(tr_row['cells']):
                        print("[Test] Current cell: ", cell)
                        if cell_idx == 0:
                            print("[Test] Cell idx = 0")
                            if current_num_cols == 1 and is_next_row_after_labels:
                                is_next_row_after_labels = False
                                for current_pane_idx in range(len(current_panes) - 1):
                                    final_pane = {'pane': current_panes[current_pane_idx], 'header': 'Test header', 'subheader': 'Test subheader'}
                                    print("[Test] Adding this to final panes:", final_pane)
                                    all_panes.append(final_pane)
                                
                                if len(current_panes) > 0:
                                    current_panes_temp = current_panes.copy()
                                    current_panes = list()
                                    current_panes.append(current_panes_temp[-1])
                                    print("Current panes after removal: ", current_panes)
                            
                            # Add to all current panes
                            for current_pane in current_panes:
                                # Add the row labels to all the current panes
                                current_row['cells'].append(cell)
                                current_pane['tr_rows'].append(current_row.copy())
                                print("[TEST] Added cell to pane: ", current_pane)


                                # Refresh the cells
                                current_row = tr_row.copy()
                                current_row['cells'] = []
                            continue
                        
                        # Append the index appropriate cell to the pane
                        current_panes[cell_idx - 1]['tr_rows'][-1]['cells'].append(cell)
                        print("Current panes: ", current_panes)
                    
            # Go through all the current panes and add them to all_panes
            for current_pane in current_panes:
                final_pane = {'pane': current_pane, 'header': 'Test header', 'subheader': 'Test subheader'}
                all_panes.append(final_pane)
            
            current_panes = []
        
        first_panel_flag = True
        for each_pane in all_panes:
            if first_panel_flag:
                panel = ParadigmExpansionPanel(
                                is_first = first_panel_flag,
                                dynamic_height= len(each_pane['pane']['tr_rows']) * 80,
                                icon="bookshelf",
                                content=ParadigmLabelContent(each_pane['pane']),
                                panel_cls=MDExpansionPanelTwoLine(
                                    text= each_pane['header'],
                                    secondary_text= each_pane['subheader']
                                )
                                )
                first_panel_flag = False
                self.add_widget(panel)
            else:
                self.add_widget(ParadigmExpansionPanel(
                                is_first = first_panel_flag,
                                dynamic_height= 0,
                                icon="bookshelf",
                                content=ParadigmLabelContent(each_pane['pane']),
                                panel_cls=MDExpansionPanelTwoLine(
                                    text= each_pane['header'],
                                    secondary_text= each_pane['subheader']
                                )
                                ))
        
    def play_sound(self, *args):
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
        elif audio_fetch_status == 4:
            # No audio found
            app.spinner2_active = False
            toast("Audio currently unavailable.")
            return
        
        # Instead of audio URL, play the file just loaded
        sound = SoundLoader.load(SOUND_FILE_NAME)
        if sound:
            print("Playing sound...")
            sound.on_stop = self.stop_loader
            sound.play()
        
    def stop_loader(self):
        app = App.get_running_app()
        app.spinner2_active = False
        

class MorphodictApp(MDApp):
    legend_of_abbr_text = LEGEND_OF_ABBREVIATIONS_TEXT
    contact_us_text = CONTACT_US_TEXT
    about_text_source_material = ABOUT_TEXT_SOURCE_MATERIALS
    about_text_credit = ABOUT_TEXT_CREDITS
    spinner2_active = BooleanProperty(defaultvalue = False)
    # result_default_size = NumericProperty(defaultvalue = dp(200))
    main_loader_active = BooleanProperty(defaultvalue = False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.menu = None
        self.index_selected = 0
        self.index_selected_paradigms = 0
        self.paradigm_labels_menu = None
        self.display_emoji_mode = False
        self.display_inflectional_category = False
        self.last_result_list_index_click = None
        self.newest_result_list = []
        self.label_type_list = ["SRO(êîôâ)", "SRO(ēīōā)", "Syllabics"]
        self.paradigm_label_type_list = ["Plain English Labels", "Linguistic labels", "nêhiyawêwin labels"]
        self.paradigm_pane_layouts_available = ["NA", "VII", "VAI", "NAD", "NI", "NID", "VTA", "VTI"]
    
    def build(self):
        # self.theme_cls.theme_style = "Dark"  # "Light" - comment this on for dark theme.
        Window.clearcolor = (0.933, 1, 0.92, 1)
        
        # Add properties to store if they don't exist
        store = JsonStore('store.json')
        if not store.exists("label_type"):
            store.put('label_type', index_selected=0)
        else:
            self.index_selected = store.get('label_type')['index_selected']
        
        self.root.ids.label_settings_dropdown.set_item(self.label_type_list[self.index_selected])
        
        if not store.exists("paradigm_labels_type"):
            store.put('paradigm_labels_type', index_selected_paradigms=0)
        else:
            self.index_selected_paradigms = store.get('paradigm_labels_type')['index_selected_paradigms']
        
        self.root.ids.paradigm_label_settings_dropdown.set_item(self.paradigm_label_type_list[self.index_selected_paradigms])
        
        if not store.exists('display_emoji_mode'):
            store.put('display_emoji_mode', display_emoji_mode = False)
        else:
            self.display_emoji_mode = store.get('display_emoji_mode')['display_emoji_mode']
        self.root.ids.display_emoji_switch.active = self.display_emoji_mode
        
        if not store.exists('display_inflectional_category'):
            store.put('display_inflectional_category', display_inflectional_category = True)
        else:
            self.display_inflectional_category = store.get('display_inflectional_category')['display_inflectional_category']
        self.root.ids.inflectional_switch.active = self.display_inflectional_category
        
        
        # Label Settings Menu
        label_settings_items = [{'index': 0, 
                                 'text': "SRO(êîôâ)", 
                                 "viewclass": "LabelSettingsItem", 
                                 "on_release": lambda x=f"SRO(êîôâ)": self.set_item(x),
                                 "text_color": (0.543, 0, 0, 1) if self.index_selected == 0 else (0, 0, 0, 1)},
                                {'index': 1, 'text': "SRO(ēīōā)", 
                                 "viewclass": "LabelSettingsItem", 
                                 "on_release": lambda x=f"SRO(ēīōā)": self.set_item(x),
                                 "text_color": (0.543, 0, 0, 1) if self.index_selected == 1 else (0, 0, 0, 1)},
                                {'index': 2, 
                                 'text': "Syllabics", 
                                 "viewclass": "LabelSettingsItem", 
                                 "on_release": lambda x=f"Syllabics": self.set_item(x),
                                 "text_color": (0.543, 0, 0, 1) if self.index_selected == 2 else (0, 0, 0, 1)}]
        
        self.menu = MDDropdownMenu(
            caller=self.root.ids.label_settings_dropdown,
            items=label_settings_items,
            width_mult=4,
        )
        
        paradigm_settings_items = [{'index': 0, 
                                 'text': "Plain English Labels", 
                                 "viewclass": "LabelSettingsItem", 
                                 "on_release": lambda x=f"Plain English Labels": self.set_item_paradigm(x),
                                 "text_color": (0.543, 0, 0, 1) if self.index_selected_paradigms == 0 else (0, 0, 0, 1)},
                                {'index': 1, 'text': "Linguistic labels", 
                                 "viewclass": "LabelSettingsItem", 
                                 "on_release": lambda x=f"Linguistic labels": self.set_item_paradigm(x),
                                 "text_color": (0.543, 0, 0, 1) if self.index_selected_paradigms == 1 else (0, 0, 0, 1)},
                                {'index': 2, 
                                 'text': "nêhiyawêwin labels", 
                                 "viewclass": "LabelSettingsItem", 
                                 "on_release": lambda x=f"nêhiyawêwin labels": self.set_item_paradigm(x),
                                 "text_color": (0.543, 0, 0, 1) if self.index_selected_paradigms == 2 else (0, 0, 0, 1)}]
        
        self.paradigm_labels_menu = MDDropdownMenu(
            caller=self.root.ids.paradigm_label_settings_dropdown,
            items=paradigm_settings_items,
            width_mult=4,
        )
        
    
    def set_item(self, text_item):
        if self.root.ids.label_settings_dropdown.current_item == text_item:
            # Same option chosen, don't do anything
            return
        
        store = JsonStore('store.json')
        
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
            store.put('label_type', index_selected=2)
        elif text_item == "SRO(ēīōā)":
            label_settings_items[1]["text_color"] = (0.543, 0, 0, 1)
            self.index_selected = 1
            store.put('label_type', index_selected=1)
        else:
            label_settings_items[0]["text_color"] = (0.543, 0, 0, 1)
            self.index_selected = 0
            store.put('label_type', index_selected=0)
        
        self.menu.items = label_settings_items
        self.root.ids.label_settings_dropdown.set_item(text_item)
        self.root.ids.main_box_layout.on_submit_word()
        second_page_population_list = self.root.ids.specific_result_main_list
        self.root.ids.specific_result_main_list.populate_page(second_page_population_list.title,
                                                              second_page_population_list.emojis, 
                                                              second_page_population_list.subtitle,
                                                              second_page_population_list.default_title,
                                                              second_page_population_list.inflectional_category,
                                                              second_page_population_list.paradigm_type,
                                                              second_page_population_list.lemma_paradigm_type,
                                                              second_page_population_list.definitions)
        self.menu.dismiss()
    
    def set_item_paradigm(self, text_item):
        if self.root.ids.paradigm_label_settings_dropdown.current_item == text_item:
            # Same option chosen, don't do anything
            return
        
        store = JsonStore('store.json')
        app = App.get_running_app()
        
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
            store.put('paradigm_labels_type', index_selected_paradigms=2)
        elif text_item == "Linguistic labels":
            paradigm_settings_items[1]["text_color"] = (0.543, 0, 0, 1)
            self.index_selected_paradigms = 1
            store.put('paradigm_labels_type', index_selected_paradigms=1)
        else:
            paradigm_settings_items[0]["text_color"] = (0.543, 0, 0, 1)
            self.index_selected_paradigms = 0
            store.put('paradigm_labels_type', index_selected_paradigms=0)
        
        self.paradigm_labels_menu.items = paradigm_settings_items
        self.root.ids.paradigm_label_settings_dropdown.set_item(text_item)
        
        # Make additional callbacks here
        self.root.ids.main_box_layout.on_submit_word()
        second_page_population_list = self.root.ids.specific_result_main_list
        self.root.ids.specific_result_main_list.populate_page(second_page_population_list.title,
                                                              second_page_population_list.emojis, 
                                                              app.newest_result_list[app.last_result_list_index_click]['subtitle'] if app.last_result_list_index_click is not None else "",
                                                              second_page_population_list.default_title,
                                                              second_page_population_list.inflectional_category,
                                                              second_page_population_list.paradigm_type,
                                                              second_page_population_list.lemma_paradigm_type,
                                                              second_page_population_list.definitions)
        
        
        self.paradigm_labels_menu.dismiss()

    @mainthread
    def main_loader_spinner_toggle(self):
        app = self.get_running_app()
        if app.root.ids.main_loader_spinner.active == False:
            app.root.ids.main_loader_spinner.active = True
            self.main_loader_active = True
        else:
            app.root.ids.main_loader_spinner.active = False
            self.main_loader_active = False

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
    # Run the main app
    MorphodictApp().run()