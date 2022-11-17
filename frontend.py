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

from uiToBackendConnector import getSearchResultsFromQuery
from api.api import get_sound
from shared.generalData import SOUND_FILE_NAME, LEGEND_OF_ABBREVIATIONS_TEXT, CONTACT_US_TEXT, HELP_CONTACT_FORM_LINK, ABOUT_TEXT_SOURCE_MATERIALS, ABOUT_TEXT_CREDITS, ABOUT_URL_LINKS, LABEL_TYPES, PARADIGM_LABEL_TYPES, PARADIGM_PANES_AVAILABLE
from shared.generalFunctions import cells_contains_only_column_labels, is_core_column_header, replace_hats_to_lines_SRO, SoundAPIResponse
from backend.frontendShared.relabelling import relabel, relabel_source

######################################################

# Global variable declarations

######################################################

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

######################################################

# Custom component declarations

######################################################

class ClickableLabel(ButtonBehavior, MDLabel):
    pass

class ClickableImage(ButtonBehavior, Image):
    pass

class InfoTooltipButton(MDIconButton, MDTooltip):
    pass

class MainLoaderSpinner(MDSpinner):
    pass

class SoundLoadSpinner(MDSpinner):
    pass

class AboutMDList(MDList):
    pass

class DrawerList(MDList):
    pass

class LabelSettingsItem(OneLineListItem):
    text = StringProperty()

######################################################

# Custom screens declarations

######################################################

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

######################################################

# Logic componenents

######################################################

class ParadigmExpansionPanel(MDExpansionPanel):
    '''
    This class represents each paradigm panel added on the second specific result page.
    '''
    def __init__(self, isFirst, dynamicHeight, **kwargs ):
        super().__init__(**kwargs)
        self.isFirst = isFirst
        self.dynamicHeight = dynamicHeight
        Clock.schedule_once(self.openFirstPanel, 0)
    def openFirstPanel(self, args):
        if self.isFirst:
            self.height += self.dynamicHeight
            self.open_panel()

class EmojiSwitch(MDCheckbox):
    '''
    This class represents the emoji display switch in the options of drawer navigation.
    '''
    def changeMode(self, currentQuery, lingMode):
        searchResultsList = getSearchResultsFromQuery(currentQuery, lingMode)
        Clock.schedule_once(partial(self.updateEmojiForUI, searchResultsList))
        time.sleep(1)
    
    def updateEmojiForUI(self, prefetched_list, *args):
        app = App.get_running_app()
        store = JsonStore('store.json')
        if self.active:
            app.displayEmojiMode = True
            store.put('displayEmojiMode', displayEmojiMode = True)
        else:
            app.displayEmojiMode = False
            store.put('displayEmojiMode', displayEmojiMode = False)
        
        app.root.ids.mainBoxLayout.onSubmitWord(prefetchedSearchResultsList=prefetched_list)
        specificResultPagePopulationList = app.root.ids.specificResultPageMainListLayout
        app.root.ids.specificResultPageMainListLayout.populate_page( specificResultPagePopulationList.title,
                                                              specificResultPagePopulationList.emojis,
                                                              app.latestSpecificResultPageMainList[app.latestResultClickIndex]['subtitle'] if app.latestResultClickIndex is not None else "",
                                                              specificResultPagePopulationList.defaultTitleText,
                                                              specificResultPagePopulationList.inflectionalCategory,
                                                              specificResultPagePopulationList.paradigm_type,
                                                              specificResultPagePopulationList.lemmaParadigmType,
                                                              specificResultPagePopulationList.definitions)
        app.main_loader_spinner_toggle()

    def emoji_display_thread(self):
        app = App.get_running_app()
        app.main_loader_spinner_toggle()

        current_query = app.root.ids.input_word.text
        
        lingMode = "community"
        
        if app.selectedParadigmOptionIndex == 1:
            lingMode = "linguistic"
        elif app.selectedParadigmOptionIndex == 2:
            lingMode = "source_language"

        threading.Thread(target=(self.changeMode), args=[current_query, lingMode]).start()

class InflectionalSwitch(MDCheckbox):
    '''
    This class represents the inflectional category display switch
    in the options of drawer navigation.
    '''
    def changeMode(self):
        app = App.get_running_app()
        store = JsonStore('store.json')
        if self.active:
            app.displayInflectionalCategory = True
            store.put('displayInflectionalCategory', displayInflectionalCategory = True)
        else:
            app.displayInflectionalCategory = False
            store.put('displayInflectionalCategory', displayInflectionalCategory = False)
        
        app.root.ids.mainBoxLayout.onSubmitWord()
        specificResultPagePopulationList = app.root.ids.specificResultPageMainListLayout
        app.root.ids.specificResultPageMainListLayout.populate_page( specificResultPagePopulationList.title,
                                                              specificResultPagePopulationList.emojis, 
                                                              app.latestSpecificResultPageMainList[app.latestResultClickIndex]['subtitle'] if app.latestResultClickIndex is not None else "",
                                                              specificResultPagePopulationList.defaultTitleText,
                                                              specificResultPagePopulationList.inflectionalCategory,
                                                              specificResultPagePopulationList.paradigm_type,
                                                              specificResultPagePopulationList.lemmaParadigmType,
                                                              specificResultPagePopulationList.definitions)

class ParadigmLabelContent(MDBoxLayout):
    '''
    This class represents the main box layout of paradigm panes in the main list.
    We just attach one copy of this class to the main layout MDList.
    '''
    
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
        
        # Prepare the paradigm data and add it to the screen
        for row in self.data['tr_rows']:
            row_box_layout = MDBoxLayout(height="40dp", size_hint = (1, None))
            if row['is_header']:
                txt_label = relabel(row['label'], paradigm_parameter[app.selectedParadigmOptionIndex])
                
                if app.selectedParadigmOptionIndex == 2:
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
                        paradigmLabelText = relabel(cell['label'], paradigm_parameter[app.selectedParadigmOptionIndex])

                        if app.selectedParadigmOptionIndex == 2:
                            paradigmLabelText = app.get_syllabics_sro_correct_label(paradigmLabelText)
                            paradigmLabelText = "[font=bjcrus.ttf]" + paradigmLabelText + "[/font]"
                        
                        paradigmLabelText = "[i]" + paradigmLabelText + "[/i]"
                        
                        row_box_layout.add_widget(Label(text = paradigmLabelText,
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
    '''
    This is the navigation manager within the app.
    Any screen changes should be declared here.
    '''
    def __init__(self, **kwargs):
        super(WindowManager, self).__init__(**kwargs)
    
    def switch_to_result_screen(self, _, title, emojis, subtitle, defaultTitleText, inflectionalCategory, paradigm_type, definitions):
        root = App.get_running_app().root
        root.ids.specificResultPageMainListLayout.populate_page(title, emojis, subtitle, defaultTitleText, inflectionalCategory, paradigm_type, None, definitions)
        self.transition.direction = "left"
        self.current = "Result"
    
    def launchSpecificResultPageOnLemmaClick(self, lemma, _, emojis, subtitle, defaultTitleText, inflectionalCategory, paradigm_type, lemmaParadigmType, definitions):
        root = App.get_running_app().root
        # root.ids.option_clicked.text = lemma
        root.ids.specificResultPageMainListLayout.populate_page(lemma, emojis, subtitle, defaultTitleText, inflectionalCategory, paradigm_type, lemmaParadigmType, definitions)
        self.transition.direction = "left"
        self.current = "Result"
    
    def switch_back_home_screen(self):
        self.transition.direction = "right"
        self.current = "Home"
    
    def switch_to_legend_screen(self):
        root = App.get_running_app().root
        root.ids.drawerNavigator.set_state("close")
        self.current = "Legend"
    
    def switch_to_contact_screen(self):
        root = App.get_running_app().root
        root.ids.drawerNavigator.set_state("close")
        self.current = "Contact"
    
    def switch_to_about_screen(self):
        root = App.get_running_app().root
        root.ids.drawerNavigator.set_state("close")
        self.current = "About"

class MainLayout(BoxLayout):
    '''
    This class is the main layout of the app (the first launch page).
    '''
    def onSubmitWord(self, widget= None, prefetchedSearchResultsList = None):
        root = App.get_running_app().root
        app = App.get_running_app()
        
        current_query = root.ids.input_word.text
        
        if not current_query:
            # Empty query
            print("Empty query")
            return
        
        lingMode = "community"
        
        if app.selectedParadigmOptionIndex == 1:
            lingMode = "linguistic"
        elif app.selectedParadigmOptionIndex == 2:
            lingMode = "source_language"
        
        output_res = prefetchedSearchResultsList

        if prefetchedSearchResultsList is None:
            output_res = getSearchResultsFromQuery(current_query, lingMode)
        
        resultToPrint = output_res.copy()
        self.displayResultList(resultToPrint)
    
    def displayResultList(self, data_list):
        '''
        This method goes through the output from the backend and serializes
        it to make it UI-friendly.
        '''
        initialSearchResultsList = []
        
        result_id_counter = 0
        
        app = App.get_running_app()
        
        for data in data_list:
            title = data['lemma_wordform']['text'] if data['is_lemma'] else data['wordform_text']
            defaultTitleText = data['lemma_wordform']['text'] if data['is_lemma'] else data['wordform_text']
            
            paradigm_type = data['lemma_wordform']['paradigm'] if data['is_lemma'] else None
            lemmaParadigmType = None
            
            # Note that the ic can also be set using relabel_plain_english and relabel_linguistic_long
            
            inflectionalCategory = data['lemma_wordform']['inflectional_category'] if data['is_lemma'] or (not data['is_lemma'] and data['show_form_of']) else "None"
            ic = data['lemma_wordform']['inflectional_category_plain_english']
            
            if app.selectedParadigmOptionIndex == 1:
                ic =  data['lemma_wordform']['inflectional_category_linguistic'] 
                if ic is not None and 'linguist_info' in data['lemma_wordform'] and data['lemma_wordform']['linguist_info']['inflectional_category'] is not None:
                    ic += " (" + data['lemma_wordform']['linguist_info']['inflectional_category'] + ")"
            
            if app.selectedParadigmOptionIndex == 2 and inflectionalCategory != "None":
                ic = relabel_source(inflectionalCategory)
            
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
            
            defaultLemmaTitleText = data['lemma_wordform']['text']
            
            if app.labelTypeIndexSelected == 2:
                # Syllabics selected
                title = sro2syllabics(title)
                if not data['is_lemma'] and data['show_form_of']:
                    data['lemma_wordform']['text'] = sro2syllabics(data['lemma_wordform']['text'])
            elif app.labelTypeIndexSelected == 1:
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
                lemmaParadigmType = data['lemma_wordform']['paradigm']
                dynamic_tile_height += 15
                for d in lemma_definitions:
                    dynamic_tile_height += 30
                    dynamic_tile_height += int(ceil(len(d) / 30)) * 35
            
            # If linguistic mode, increase dynamic height to give space for the larger subtitle
            if app.selectedParadigmOptionIndex == 1 or app.selectedParadigmOptionIndex == 2:
                dynamic_tile_height += 20
            
               
            initialSearchResultsList.append({'index': result_id_counter,
                                        'defaultTitleText': defaultTitleText,
                                        'height': dp(max(100, dynamic_tile_height)),
                                        'title': title, 
                                        'emojis': emojis, 
                                        'subtitle': subtitle,
                                        'inflectionalCategory': inflectionalCategory,
                                        'paradigm_type': paradigm_type,
                                        'lemmaParadigmType': lemmaParadigmType,
                                        'lemma_definitions': lemma_definitions,
                                        'friendly_linguistic_breakdown_head': data['friendly_linguistic_breakdown_head'],
                                        'friendly_linguistic_breakdown_tail': data['friendly_linguistic_breakdown_tail'],
                                        'relabelled_fst_analysis': data['relabelled_fst_analysis'],
                                        'is_lemma': data['is_lemma'] if 'is_lemma' in data else True,
                                        'show_form_of': data['show_form_of'] if 'show_form_of' in data else False,
                                        'defaultLemmaTitleText': defaultLemmaTitleText,
                                        'lemma_wordform': data['lemma_wordform'] if 'lemma_wordform' in data else None,
                                        'definitions': defsToPass
                                        })
            
            result_id_counter += 1
        
        if len(initialSearchResultsList) == 0:
            root = App.get_running_app().root
            initialSearchResultsList.append({'index': -1, 'title': 'No results found!', 'definitions': [root.ids.input_word.text]})
        
        root = App.get_running_app().root
        
        root.ids.result_list_main.update_data(initialSearchResultsList)

class ResultView(RecycleView):
    def __init__(self, **kwargs):
        super(ResultView, self).__init__(**kwargs)
        self.data = []
    
    def update_data(self, data):
        app = App.get_running_app()
        self.data = data.copy()
        app.latestSpecificResultPageMainList = data.copy()
        self.refresh_from_data()

class ResultWidget(RecycleDataViewBehavior, MDBoxLayout):
    '''
    This class represents the view class of every result from the search query
    on the main page (results list page).
    '''
    _latest_data = None
    _rv = None
    
    index = ObjectProperty()
    defaultTitleText = ObjectProperty()
    title = ObjectProperty()
    subtitle = ObjectProperty()
    emojis = ObjectProperty()
    inflectionalCategory = ObjectProperty()
    paradigm_type = ObjectProperty(allownone = True)
    lemmaParadigmType = ObjectProperty(allownone = True)
    lemma_definitions = ObjectProperty()
    friendly_linguistic_breakdown_head = ObjectProperty()
    friendly_linguistic_breakdown_tail = ObjectProperty()
    relabelled_fst_analysis = ObjectProperty()
    is_lemma = ObjectProperty()
    show_form_of = ObjectProperty()
    defaultLemmaTitleText = ObjectProperty()
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
            
            if app.displayInflectionalCategory:
                inflection_label = Label(text="[size=15dp]" + self.inflectionalCategory + "[/size]", markup=True)
                inflection_label._label.refresh()
                inflection_label = MDLabel(text="[size=15dp]" + self.inflectionalCategory + "[/size]", 
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
            
            
            if app.displayEmojiMode == True:
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
        if app.displayInflectionalCategory:
            inflection_label = Label(text="[size=15dp]" + self.inflectionalCategory + "[/size]", markup=True)
            inflection_label._label.refresh()
            inflection_label = MDLabel(text="[size=15dp]" + self.inflectionalCategory + "[/size]", 
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
        
        if app.displayEmojiMode == True:
            description_box_layout.add_widget(emoji_label)
        description_box_layout.add_widget(desc_label)
        
        self.add_widget(description_box_layout)
        
        definitions_to_display = self.definitions
        if not self.is_lemma and self.show_form_of:
            definitions_to_display = self.lemma_definitions
        
        for definition in definitions_to_display:
            definition_label = MDLabel(text="[size=14dp]" + definition + "[/size]", markup = True)
            self.add_widget(definition_label)
        
    def on_click_label(self, touch):
        if not self.is_lemma and self.show_form_of:
            # Shouldn't be clicked/redirected.
            return
        app = App.get_running_app()
        root = App.get_running_app().root
        app.latestResultClickIndex = self.index
        root.ids.screen_manager.switch_to_result_screen(self.index, self.title, self.emojis, self.subtitle, self.defaultTitleText, self.inflectionalCategory, self.paradigm_type, self.definitions)
    
    def on_click_form_of_lemma(self, touch):
        root = App.get_running_app().root
        
        lemma = self.lemma_wordform['text']
        
        root.ids.screen_manager.launchSpecificResultPageOnLemmaClick(lemma, self.title, self.emojis, self.subtitle, self.defaultLemmaTitleText, self.inflectionalCategory, self.paradigm_type, self.lemmaParadigmType, self.definitions)
    
    def play_sound(self, touch):
        audioFetchStatus = get_sound(self.defaultTitleText)
        
        if audioFetchStatus == SoundAPIResponse.CONNECTION_ERROR:
            toast("This feature needs a reliable internet connection.")
            return
        elif audioFetchStatus == SoundAPIResponse.NO_AUDIO_AVAILABLE:
            toast("No recording available for this word.")
            return
        elif audioFetchStatus == SoundAPIResponse.API_NO_HIT:
            # No audio found
            toast("Audio currently unavailable.")
            return
        
        toast("Playing sound...", duration = 1)
        
        # Instead of audio URL, play the file just loaded
        sound = SoundLoader.load(SOUND_FILE_NAME)
        if sound:
            sound.play()
            
class SpecificResultMainList(MDList):
    '''
    This is the specific result page (2nd page) main list where
    title, description, panes, etc. are added in order.
    '''
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.title = None
        self.emojis = None
        self.subtitle = None
        self.defaultTitleText = None
        self.inflectionalCategory = None
        self.paradigm_type = None
        self.lemmaParadigmType = None
        self.definitions = None
    
    def populate_page(self, title, emojis, subtitle, defaultTitleText, inflectionalCategory, paradigm_type, lemmaParadigmType, definitions):
        '''
        Populates the second result-specific page
        '''
        self.title = title
        self.emojis = emojis
        self.subtitle = subtitle
        self.defaultTitleText = defaultTitleText
        self.inflectionalCategory = inflectionalCategory
        self.paradigm_type = paradigm_type
        self.lemmaParadigmType = lemmaParadigmType
        self.definitions = definitions
        
        app = App.get_running_app()
        root = App.get_running_app().root
        self.clear_widgets()
        
        if title is None and defaultTitleText is None and definitions is None:
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
        title_and_sound_boxlayout.add_widget(SoundLoadSpinner())
        
        
        top_details_box_layout.add_widget(title_and_sound_boxlayout)
        
        
        # Add description
        description_box_layout = MDBoxLayout(size_hint = (1, 0.5))
        
        # Add the inflectional category
        if app.displayInflectionalCategory:
            inflection_label = Label(text="[size=24]" + self.inflectionalCategory + "[/size]", markup=True)
            inflection_label._label.refresh()
            inflection_label = MDLabel(text="[size=24]" + self.inflectionalCategory + "[/size]", 
                                markup=True,
                                size_hint=(None, 1),
                                width=inflection_label._label.texture.size[0] + 5)
            
            description_box_layout.add_widget(inflection_label)
            
        additional_emoji_margin = 0 if not emojis else 10
        
        emoji_label = Label(text="[size=24][font=NotoEmoji-Regular.ttf]" + emojis + "[/font][/size]", markup=True)
        emoji_label._label.refresh()
        emoji_label = MDLabel(text="[size=24][font=NotoEmoji-Regular.ttf]" + emojis + "[/font][/size]", 
                            markup=True,
                            size_hint=(None, 1),
                            width=emoji_label._label.texture.size[0] + additional_emoji_margin)
    
        desc_label = MDLabel(text="[size=24]" + subtitle + "[/size]", markup=True)
        
        if app.displayEmojiMode:
            description_box_layout.add_widget(emoji_label)
        description_box_layout.add_widget(desc_label)
        
        top_details_box_layout.add_widget(description_box_layout)
        
        # Add definitions
        for definition in definitions:
            top_details_box_layout.add_widget(MDLabel(text = definition))
        
        self.add_widget(top_details_box_layout)
        
        # Add paradigm panes
        pane_generator = paradigm_panes.PaneGenerator()
        
        # Set the right directory paths for the pane generator
        pane_generator.set_layouts_dir(BASE_DIR + "/layouts")
        pane_generator.set_fst_filepath(BASE_DIR + "/backend/resourcesFST/crk-strict-generator.hfstol")
        
        paradigm = {'panes': []}
        
        # Check whether lemma was clicked on the "form of" line
        # or the main title for that result was clicked
        if lemmaParadigmType is None:
            # If lemma wasn't clicked, check if the current title paradigm type has a tsv
            if paradigm_type is not None and paradigm_type in app.availableParadigmPanes:
                paradigm = pane_generator.generate_pane(defaultTitleText, paradigm_type)
            elif paradigm_type is None:
                print("Paradigm Type (currently unavailable): ", paradigm_type)
                return
        elif lemmaParadigmType in app.availableParadigmPanes:
            # If lemma was clicked, check if the current lemma paradigm type has a tsv
            paradigm = pane_generator.generate_pane(defaultTitleText, lemmaParadigmType)
        else:
            # No TSV file found, don't add any panes
            print("Paradigm Type (currently unavailable): ", paradigm_type)
            return
        
        paradigm_data = paradigm.copy()
        
        # Decide how many panels to add
        all_panes = []
        header, subheader = None, None
        
        # Go through every pane
        for pane_idx, pane in enumerate(paradigm_data['panes']):
            # Reset all the initial values
            is_core_pane = False
            is_next_row_after_labels = False
            current_num_cols = 0
            current_panes = []
            # Some panes have a header row and a subheader row like VTA
            # | Prs | Ind | Prs | Cnj ...
            # | 1Sg	| 1Sg | 1Sg | ...
            # currentHeaderLabels helps record the headers for later rows
            currentHeaderLabels = []
            firstNonLabelRowInPane = True
            # Go through every row inside the pane
            for row_idx, tr_row in enumerate(pane['tr_rows']):
                # Ignore the row if it's a header row (just contains #NA for eg.)
                if not tr_row['is_header']:
                    
                    # Check if the pane is a Core pane
                    if not is_core_pane and cells_contains_only_column_labels(tr_row['cells'])[0] and is_core_column_header(tr_row['cells']):
                        header = "Core"
                        is_core_pane = True
                        continue
                    
                    # Check if a row contains only column labels
                    # If so, record the number of column labels does it contains
                    is_row_only_col_labels, num_cols = cells_contains_only_column_labels(tr_row['cells'])
                    if is_row_only_col_labels:
                        isNextRowLabelOnly, _ = cells_contains_only_column_labels(pane['tr_rows'][row_idx + 1]['cells'])
                        if isNextRowLabelOnly:
                            # Ignore the header row for now - temporary test
                            continue
                        # If it does contain only column headers, let's add num_cols panes 
                        # as those = number of panes for that "pane" in this for loop
                        current_num_cols = num_cols
                        is_next_row_after_labels = True
                        for cell_idx, cell in enumerate(tr_row['cells']):
                            # Check if it's not the first cell of the cells
                            # as that's usually empty!
                            if cell_idx != 0:
                                current_panes.append({'tr_rows': [], 'headerTitle': header, "subheaderTitle": relabel(cell['label'])})
                        # Let's look at the next row now that panes have been added
                        continue

                    # Immitate the row minus the cells that we will just recreate
                    # for every pane
                    current_row = tr_row.copy()
                    current_row['cells'] = []
                    for cell_idx, cell in enumerate(tr_row['cells']):
                        if cell_idx > current_num_cols:
                            # We enter here when there's no 1:1 mapping for column header -> single row label's value
                            # row_span > 1 not considered, we just take the first word found
                            break
                        if cell_idx == 0:
                            if is_next_row_after_labels:
                                if not firstNonLabelRowInPane:
                                    # Whenever looking at something like:
                                    # | Core
                                    #   | Poss
                                    #   ...
                                    #   | Nonposs
                                    #   ...
                                    # Whenever we hit Nonposs, make sure to add the Poss pane 
                                    # to all_panes. 
                                    # This is not required when we have current_num_cols > 1 
                                    # because they don't have only label row in middle of the output
                                    # so can be added in the end
                                    is_next_row_after_labels = False
                                    for current_pane_idx in range(len(current_panes) - 1):
                                        final_pane = {'pane': current_panes[current_pane_idx], 'header': current_panes[current_pane_idx]['headerTitle'], 'subheader': current_panes[current_pane_idx]['subheaderTitle']}
                                        all_panes.append(final_pane)
                                    
                                    # Now that current panes so far have been added to all_panes,
                                    # reset the current_panes list to just contain the current row (which is on -1 idx)
                                    if len(current_panes) > 0:
                                        current_panes_temp = current_panes.copy()
                                        current_panes = list()
                                        current_panes.append(current_panes_temp[-1])
                                else:
                                    firstNonLabelRowInPane = False
                                    is_next_row_after_labels = False
                            
                            # Update the current_pane to include the new cell found in this iteration
                            for current_pane in current_panes:
                                # Add the row labels to all the current panes
                                current_row['cells'].append(cell)
                                current_pane['tr_rows'].append(current_row.copy())


                                # Refresh the cells
                                current_row = tr_row.copy()
                                current_row['cells'] = []
                            continue
                        
                        # Append the index appropriate cell to the pane
                        current_panes[cell_idx - 1]['tr_rows'][-1]['cells'].append(cell)
                    
            # End of a "pane", add all the panes in current_panes to all_panes
            for current_pane in current_panes:
                final_pane = {'pane': current_pane, 'header': current_pane['headerTitle'], 'subheader': current_pane['subheaderTitle']}
                all_panes.append(final_pane)
            
            current_panes = []
        
        first_panel_flag = True
        for each_pane in all_panes:
            if first_panel_flag:
                # If first pane, we need to open it initially
                panel = ParadigmExpansionPanel(
                                isFirst = first_panel_flag,
                                dynamicHeight= dp(len(each_pane['pane']['tr_rows']) * 60),
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
                # If not the first pane, no need to open it initially so dynamicHeight doesn't matter
                # Note that dynamicHeight is only used for initial opening purposes
                self.add_widget(ParadigmExpansionPanel(
                                isFirst = first_panel_flag,
                                dynamicHeight= 0,
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
        audioFetchStatus = get_sound(self.defaultTitleText)
        
        if audioFetchStatus == SoundAPIResponse.CONNECTION_ERROR:
            app.spinner2_active = False
            toast("This feature needs a reliable internet connection.")
            return
        elif audioFetchStatus == SoundAPIResponse.NO_AUDIO_AVAILABLE:
            app.spinner2_active = False
            toast("No recording available for this word.")
            return
        elif audioFetchStatus == SoundAPIResponse.API_NO_HIT:
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
        

######################################################

# Main application class

######################################################

class MorphodictApp(MDApp):
    legend_of_abbr_text = LEGEND_OF_ABBREVIATIONS_TEXT
    contact_us_text = CONTACT_US_TEXT
    about_text_source_material = ABOUT_TEXT_SOURCE_MATERIALS
    about_text_credit = ABOUT_TEXT_CREDITS
    spinner2_active = BooleanProperty(defaultvalue = False)
    main_loader_active = BooleanProperty(defaultvalue = False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.menu = None
        self.labelTypeIndexSelected = 0
        self.selectedParadigmOptionIndex = 0
        self.paradigmLabelsMenu = None
        self.displayEmojiMode = False
        self.displayInflectionalCategory = False
        self.latestResultClickIndex = None
        self.latestSpecificResultPageMainList = []
        self.labelTypeList = LABEL_TYPES
        self.paradigmLabelType = PARADIGM_LABEL_TYPES
        self.availableParadigmPanes = PARADIGM_PANES_AVAILABLE
    
    def build(self):
        # self.theme_cls.theme_style = "Dark"  # "Light" - comment this on for dark theme.
        Window.clearcolor = (0.933, 1, 0.92, 1)
        
        # Add properties to store if they don't exist
        store = JsonStore('store.json')
        if not store.exists("label_type"):
            store.put('label_type', labelTypeIndexSelected=0)
        else:
            self.labelTypeIndexSelected = store.get('label_type')['labelTypeIndexSelected']
        
        self.root.ids.labelSettingsDropdown.set_item(self.labelTypeList[self.labelTypeIndexSelected])
        
        if not store.exists("paradigmLabelsType"):
            store.put('paradigmLabelsType', selectedParadigmOptionIndex=0)
        else:
            self.selectedParadigmOptionIndex = store.get('paradigmLabelsType')['selectedParadigmOptionIndex']
        
        self.root.ids.paradigmSettingsDropdown.set_item(self.paradigmLabelType[self.selectedParadigmOptionIndex])
        
        if not store.exists('displayEmojiMode'):
            store.put('displayEmojiMode', displayEmojiMode = False)
        else:
            self.displayEmojiMode = store.get('displayEmojiMode')['displayEmojiMode']
        self.root.ids.display_emoji_switch.active = self.displayEmojiMode
        
        if not store.exists('displayInflectionalCategory'):
            store.put('displayInflectionalCategory', displayInflectionalCategory = True)
        else:
            self.displayInflectionalCategory = store.get('displayInflectionalCategory')['displayInflectionalCategory']
        self.root.ids.inflectionalSwitch.active = self.displayInflectionalCategory
        
        
        # Label Settings Menu
        label_settings_items = [{'index': 0, 
                                 'text': "SRO(êîôâ)", 
                                 "viewclass": "LabelSettingsItem", 
                                 "on_release": lambda x=f"SRO(êîôâ)": self.set_item(x),
                                 "text_color": (0.543, 0, 0, 1) if self.labelTypeIndexSelected == 0 else (0, 0, 0, 1)},
                                {'index': 1, 'text': "SRO(ēīōā)", 
                                 "viewclass": "LabelSettingsItem", 
                                 "on_release": lambda x=f"SRO(ēīōā)": self.set_item(x),
                                 "text_color": (0.543, 0, 0, 1) if self.labelTypeIndexSelected == 1 else (0, 0, 0, 1)},
                                {'index': 2, 
                                 'text': "Syllabics", 
                                 "viewclass": "LabelSettingsItem", 
                                 "on_release": lambda x=f"Syllabics": self.set_item(x),
                                 "text_color": (0.543, 0, 0, 1) if self.labelTypeIndexSelected == 2 else (0, 0, 0, 1)}]
        
        self.menu = MDDropdownMenu(
            caller=self.root.ids.labelSettingsDropdown,
            items=label_settings_items,
            width_mult=4,
        )
        
        paradigmSettingsItems = [{'index': 0, 
                                 'text': "Plain English Labels", 
                                 "viewclass": "LabelSettingsItem", 
                                 "on_release": lambda x=f"Plain English Labels": self.set_item_paradigm(x),
                                 "text_color": (0.543, 0, 0, 1) if self.selectedParadigmOptionIndex == 0 else (0, 0, 0, 1)},
                                {'index': 1, 'text': "Linguistic labels", 
                                 "viewclass": "LabelSettingsItem", 
                                 "on_release": lambda x=f"Linguistic labels": self.set_item_paradigm(x),
                                 "text_color": (0.543, 0, 0, 1) if self.selectedParadigmOptionIndex == 1 else (0, 0, 0, 1)},
                                {'index': 2, 
                                 'text': "nêhiyawêwin labels", 
                                 "viewclass": "LabelSettingsItem", 
                                 "on_release": lambda x=f"nêhiyawêwin labels": self.set_item_paradigm(x),
                                 "text_color": (0.543, 0, 0, 1) if self.selectedParadigmOptionIndex == 2 else (0, 0, 0, 1)}]
        
        self.paradigmLabelsMenu = MDDropdownMenu(
            caller=self.root.ids.paradigmSettingsDropdown,
            items=paradigmSettingsItems,
            width_mult=4,
        )
        
    
    def set_item(self, text_item):
        if self.root.ids.labelSettingsDropdown.current_item == text_item:
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
            self.labelTypeIndexSelected = 2
            store.put('label_type', labelTypeIndexSelected=2)
        elif text_item == "SRO(ēīōā)":
            label_settings_items[1]["text_color"] = (0.543, 0, 0, 1)
            self.labelTypeIndexSelected = 1
            store.put('label_type', labelTypeIndexSelected=1)
        else:
            label_settings_items[0]["text_color"] = (0.543, 0, 0, 1)
            self.labelTypeIndexSelected = 0
            store.put('label_type', labelTypeIndexSelected=0)
        
        self.menu.items = label_settings_items
        self.root.ids.labelSettingsDropdown.set_item(text_item)
        self.root.ids.mainBoxLayout.onSubmitWord()
        specificResultPagePopulationList = self.root.ids.specificResultPageMainListLayout
        self.root.ids.specificResultPageMainListLayout.populate_page(specificResultPagePopulationList.title,
                                                              specificResultPagePopulationList.emojis, 
                                                              specificResultPagePopulationList.subtitle,
                                                              specificResultPagePopulationList.defaultTitleText,
                                                              specificResultPagePopulationList.inflectionalCategory,
                                                              specificResultPagePopulationList.paradigm_type,
                                                              specificResultPagePopulationList.lemmaParadigmType,
                                                              specificResultPagePopulationList.definitions)
        self.menu.dismiss()
    
    def set_item_paradigm(self, text_item):
        if self.root.ids.paradigmSettingsDropdown.current_item == text_item:
            # Same option chosen, don't do anything
            return
        
        store = JsonStore('store.json')
        app = App.get_running_app()
        
        paradigmSettingsItems = [{'index': 0, 
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
            paradigmSettingsItems[2]["text_color"] = (0.543, 0, 0, 1)
            self.selectedParadigmOptionIndex = 2
            store.put('paradigmLabelsType', selectedParadigmOptionIndex=2)
        elif text_item == "Linguistic labels":
            paradigmSettingsItems[1]["text_color"] = (0.543, 0, 0, 1)
            self.selectedParadigmOptionIndex = 1
            store.put('paradigmLabelsType', selectedParadigmOptionIndex=1)
        else:
            paradigmSettingsItems[0]["text_color"] = (0.543, 0, 0, 1)
            self.selectedParadigmOptionIndex = 0
            store.put('paradigmLabelsType', selectedParadigmOptionIndex=0)
        
        self.paradigmLabelsMenu.items = paradigmSettingsItems
        self.root.ids.paradigmSettingsDropdown.set_item(text_item)
        
        # Make additional callbacks here
        self.root.ids.mainBoxLayout.onSubmitWord()
        specificResultPagePopulationList = self.root.ids.specificResultPageMainListLayout
        self.root.ids.specificResultPageMainListLayout.populate_page(specificResultPagePopulationList.title,
                                                              specificResultPagePopulationList.emojis, 
                                                              app.latestSpecificResultPageMainList[app.latestResultClickIndex]['subtitle'] if app.latestResultClickIndex is not None else "",
                                                              specificResultPagePopulationList.defaultTitleText,
                                                              specificResultPagePopulationList.inflectionalCategory,
                                                              specificResultPagePopulationList.paradigm_type,
                                                              specificResultPagePopulationList.lemmaParadigmType,
                                                              specificResultPagePopulationList.definitions)
        
        
        self.paradigmLabelsMenu.dismiss()

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
                            ]
        
        for drawer_item in drawer_items_list:
            row_item = OneLineIconListItem(text=drawer_item['text'], on_release=drawer_item['callback'])
            row_item.add_widget(IconLeftWidget(icon=drawer_item['icon']))
            self.root.ids.navigation_drawer_list.add_widget(row_item)
        return super().on_start()

    def on_legend_ref_press(self, instance, ref):
        root = App.get_running_app().root
        root.ids.input_word.text = ref
        root.ids.mainBoxLayout.onSubmitWord()
        root.ids.screen_manager.switch_back_home_screen()
    
    def on_contact_ref_press(self, instance, ref):
        webbrowser.open(HELP_CONTACT_FORM_LINK)
        
    def on_about_ref_press(self, instance, ref):
        webbrowser.open(ABOUT_URL_LINKS[ref])
    
    def get_syllabics_sro_correct_label(self, string: str) -> str:
        if self.labelTypeIndexSelected == 2:
            # Syllabics
            string = sro2syllabics(string)
        elif self.labelTypeIndexSelected == 1:
            # ēīōā selected
            string = replace_hats_to_lines_SRO(string)
        
        return string