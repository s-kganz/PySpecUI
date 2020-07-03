from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.properties import ObjectProperty, StringProperty
from kivy.factory import Factory
from kivy.uix.textinput import TextInput
from kivy.clock import Clock

# Widget classes
class AbstractParameterWidget(BoxLayout):
    '''
    Abstract parameter widget defining the interface
    that all other widgets must adhere to.
    '''
    label_text = ''
    field = ObjectProperty(None)
    def get_parameter_value(self):
        raise NotImplementedError("Parameter must define get_value()")

class IntegerParameterWidget(AbstractParameterWidget):
    '''
    A text field allowing numeric characters only.
    '''
    def __init__(self, label_text='An integer:', **kwargs):
        self.label_text = label_text
        super().__init__(**kwargs)
        Clock.schedule_once(self.add_field_widget)

    def add_field_widget(self, *args):
        w = TextInput(
            multiline = False,
            input_filter = 'int'
        )
        self.field = w
        self.ids['layout'].add_widget(w)
    
    def get_parameter_value(self):
        return int(self.field.text) if len(self.field.text) > 0 else None

class FloatParameterWidget(AbstractParameterWidget):
    '''
    A text field allowing numeric input and one decimal point.
    '''
    def __init__(self, label_text='A floating point number', **kwargs):
        self.label_text = label_text
        super().__init__(**kwargs)
        Clock.schedule_once(self.add_field_widget)
    
    def add_field_widget(self, *args):
        w = TextInput(
            multiline = False,
            input_filter = 'float'
        )
        self.field = w
        self.ids['layout'].add_widget(w)
    
    def get_parameter_value(self):
        return float(self.field.text) if len(self.field.text) > 0 else None
    
class TextParameterWidget(AbstractParameterWidget):
    '''
    A general text input.
    '''
    def __init__(self, label_text='Some text', **kwargs):
        self.label_text = label_text
        super().__init__(**kwargs)
        Clock.schedule_once(self.add_field_widget)
    
    def add_field_widget(self, *args):
        w = TextInput(
            multiline = False
        )
        self.field = w
        self.ids['layout'].add_widget(w)

    def get_parameter_value(self):
        return self.field.text

class ChoiceParameterWidget(AbstractParameterWidget):
    '''
    A widget for a dropdown menu of choices.
    '''
    def __init__(self, choices=['1', '2', '3'], label_text='Choices', **kwargs):
        self.label_text = label_text
        self.choices = choices
        super().__init__(**kwargs)
        Clock.schedule_once(self.add_field_widget)
    
    def add_field_widget(self, *args):
        w = Spinner(
            text = self.choices[0],
            values = self.choices.copy()
        )
        self.field = w
        self.ids['layout'].add_widget(w)
        del self.choices

    def get_parameter_value(self):
        return self.field.text

class Dialog(Popup):
    '''
    Base class for all popups in the application.
    '''
    def __init__(self, *args, **kwargs):
        defaults = dict(
            size_hint = (None, None),
            size = (400, 600),
            title = 'A Dialog',
            auto_dismiss = False
        )
        defaults.update(**kwargs)
        super().__init__(*args, **defaults)
        Clock.schedule_once(self._build_content_area)
    
    def _build_content_area(self, *args):
        '''
        Add all of the user-defined parameters to the dialog
        content area.
        '''
        parameters = self.define_parameters()
        for widget in parameters:
            self.ids['content_area'].add_widget(widget)
    
    def _execute(self):
        '''
        Gather all parameter widgets from the content area and pass
        to execution function.
        '''
        param_values = list(
            map(lambda p: p.get_parameter_value(),
                self.ids['content_area'].children)
        ) 
        # Children is a stack, reverse to keep in instantiation order
        param_values.reverse()
        self.execute(param_values)

    def define_parameters(self):
        '''
        Function that must be implemented by the user. Return a list of objects
        derived from AbstractParameterWidget.
        '''
        return []
    
    def execute(self, parameters):
        '''
        Function that implements tool execution. Parameters is a list of parameter
        values in the same order as the list where parameters are defined.
        '''
        raise NotImplementedError("Tool execution must be defined.")

class TestDialog(Dialog):
    '''
    Dialog that creates a parameter of each type in the application
    and prints the value associated with each parameter.
    '''
    def define_parameters(self):
        return [
            TextParameterWidget(),
            IntegerParameterWidget(),
            FloatParameterWidget(),
            ChoiceParameterWidget()
        ]
    
    def execute(self, parameters):
        for idx, val in enumerate(parameters):
            print("Parameter {}:\t{}".format(idx, val))

# Register dialogs in the factory
Factory.register('TestDialog', cls=TestDialog)