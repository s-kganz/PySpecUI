from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ObjectProperty

class HistoryEntry(BoxLayout):
    tr = ObjectProperty(None)

    def __init__(self, tr, *args, **kwargs):
        self.tr = tr
        super().__init__(**kwargs)
        

class History(BoxLayout):
    def add_entry(self, tr):
        entry = HistoryEntry(tr)
        self.ids['entry_layout'].add_widget(entry)

