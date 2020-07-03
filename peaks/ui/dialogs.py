from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.properties import ObjectProperty, StringProperty
from kivy.factory import Factory
from kivy.uix.textinput import TextInput
from kivy.clock import Clock

# Widget classes
class AbstractParameterWidget(BoxLayout):
    '''
    An abstract parameter
    '''
    field = ObjectProperty(None)
    _label_text = StringProperty(None)

class IntegerParameterWidget(AbstractParameterWidget):
    def __init__(self, label_text='An integer:', **kwargs):
        super().__init__(**kwargs)
        self.label_text = label_text
        Clock.schedule_once(self.add_field_widget)

    def add_field_widget(self, *args):
        w = TextInput(
            multiline = False,
            input_filter = 'int'
        )
        self.field = w
        self.ids['layout'].add_widget(w)

class FloatParameterWidget(AbstractParameterWidget):
    def __init__(self, label_text='A floating point number', **kwargs):
        super().__init__(**kwargs)
        self.label_text = label_text
        Clock.schedule_once(self.add_field_widget)
    
    def add_field_widget(self, *args):
        w = TextInput(
            multiline = False,
            input_filter = 'float'
        )
        self.field = w
        self.ids['layout'].add_widget(w)
    
class TextParameterWidget(AbstractParameterWidget):
    def __init__(self, label_text='Some text', **kwargs):
        super().__init__(**kwargs)
        self.label_text = 'A really long name that should wrap into multiple lines'
        Clock.schedule_once(self.add_field_widget)
    
    def add_field_widget(self, *args):
        w = TextInput(
            multiline = False
        )
        self.field = w
        self.ids['layout'].add_widget(w)


class AbstractParameter():
    '''
    Base class for widgets that take input
    from the user
    '''
    display_name = StringProperty()

    def __init__(self, display_name='', description='', validator=None, **kwargs):
        self.display_name = display_name
        self.description = description
        self.validator = validator
    
    def build_widgets(self, hook):
        raise NotImplementedError("build_widgets not implemented in AbstractParameter")

    def get_value(self):
        raise NotImplementedError("get_value not implemented in AbstractParameter")
    
class DialogPopup(Popup):
    '''
    Base class for all popups in the application.
    '''
    # Hook for adding widgets to the dialog
    _content_area = ObjectProperty(None)
    def execute(self):
        raise NotImplementedError("Tool execution must be defined.")

# Register classes
Factory.register('DialogPopup', cls=DialogPopup)