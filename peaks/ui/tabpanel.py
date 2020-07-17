from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.accordion import AccordionItem
from kivy.properties import ObjectProperty
from kivy.clock import Clock
from kivy.factory import Factory
from kivy.uix.gridlayout import GridLayout

from peaks.ui.parameters import AccordionSlider

class TunerTabItem(TabbedPanelItem):
    content_area = ObjectProperty(None)
    param_schema = ObjectProperty(None)
    callback = ObjectProperty(None)

    def __init__(self, callback, *args, **kwargs):
        super().__init__(**kwargs)
        self.callback = callback
        Clock.schedule_once(lambda *args: self._build_schema(callback.get_schema()))
    
    def _build_schema(self, schema):
        '''
        Build UI widgets and the structure of the dictionary sent back to the tunable
        '''
        self.param_schema = dict()
        for key in schema:
            self.param_schema[key] = dict()
            item = AccordionItem(title=key)
            layout = GridLayout(cols=1, spacing=20, padding=10)
            item.add_widget(layout)
            for param in schema[key]:
                widget = AccordionSlider(self, **schema[key][param], param_label=param)
                self.param_schema[key][param] = widget
                layout.add_widget(widget)
            self.content_area.add_widget(item)
    
    def update_schema(self):
        ret = dict()
        for key in self.param_schema:
            ret[key] = dict()
            for param in self.param_schema[key]:
                ret[key][param] = self.param_schema[key][param].param_value
        
        callback.set_schema(ret)


class DynamicTabbedPanel(TabbedPanel):
    def add_tuner(self, tunable):
        blank = TunerTabItem(tunable, text='Tuner')
        self.add_widget(blank)

        
Factory.register('TunerTabItem', cls=TunerTabItem)