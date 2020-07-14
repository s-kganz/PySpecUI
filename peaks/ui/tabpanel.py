from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.properties import ObjectProperty

class ScrollAccordionTabItem(TabbedPanelItem):
    content_area = ObjectProperty(None)

class DynamicTabbedPanel(TabbedPanel):
    def add_tab(self):
        blank = ScrollAccordionTabItem(text='Blank')
        self.add_widget(blank)