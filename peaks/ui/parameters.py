from kivy.properties import ObjectProperty, StringProperty, NumericProperty
from kivy.clock import Clock
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.slider import Slider
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout

__all__ = ['IntegerParameterWidget', 'FloatParameterWidget', 'TextParameterWidget',
           'ChoiceParameterWidget', 'SpectrumParameterWidget', 'FileParameterWidget',
           'FloatSliderParameterWidget', 'AccordionSlider']

class AbstractParameterWidget(BoxLayout):
    '''
    Abstract parameter widget defining the interface
    that all other widgets must adhere to.
    '''
    field = ObjectProperty(None)
    def __init__(self, label_text='', param_name='', **kwargs):
        self.label_text = label_text
        self.param_name = param_name
        super().__init__(**kwargs)
    
    def get_parameter_tuple(self):
        return self.param_name, self._get_parameter_value()

    def _get_parameter_value(self):
        raise NotImplementedError("Parameter must define get_value()")

class IntegerParameterWidget(AbstractParameterWidget):
    '''
    A text field allowing numeric characters only.
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(self.add_field_widget)

    def add_field_widget(self, *args):
        w = TextInput(
            multiline = False,
            input_filter = 'int'
        )
        self.field = w
        self.ids['layout'].add_widget(w)
    
    def _get_parameter_value(self):
        return int(self.field.text) if len(self.field.text) > 0 else None

class FloatParameterWidget(AbstractParameterWidget):
    '''
    A text field allowing numeric input and one decimal point.
    '''
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(self.add_field_widget)
    
    def add_field_widget(self, *args):
        w = TextInput(
            multiline = False,
            input_filter = 'float'
        )
        self.field = w
        self.ids['layout'].add_widget(w)
    
    def _get_parameter_value(self):
        return float(self.field.text) if len(self.field.text) > 0 else None
    
class TextParameterWidget(AbstractParameterWidget):
    '''
    A general text input.
    '''
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(self.add_field_widget)
    
    def add_field_widget(self, *args):
        w = TextInput(
            multiline = False
        )
        self.field = w
        self.ids['layout'].add_widget(w)

    def _get_parameter_value(self):
        return self.field.text

class ChoiceParameterWidget(AbstractParameterWidget):
    '''
    A widget for a dropdown menu of choices.
    '''
    def __init__(self, choices, **kwargs):
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

    def _get_parameter_value(self):
        return self.field.text

class SpectrumParameterWidget(ChoiceParameterWidget):
    '''
    A widget for a dropdown menu of spectra.
    '''  
    def __init__(self, ds, **kwargs):
        self.choice_dict = {"{} ({})".format(str(s), s.id):s \
                            for s in ds.get_all_spectra().values()}
        if len(self.choice_dict) == 0:
            self.choice_dict = {"No spectra loaded": None}
        super().__init__(list(self.choice_dict.keys()), **kwargs)
    
    def _get_parameter_value(self):
        return self.choice_dict[self.field.text]

class FileFieldWidget(BoxLayout):
    '''
    Helper class for file selection implementing a field
    to display the selected field and a button to launch
    a file selection dialog.
    '''
    text_field = ObjectProperty(None)

    def __init__(self, *args, **kwargs):
        self.max_chars = 30
        super().__init__(*args, **kwargs)
    
    def get_value(self):
        return self.text_field.text


class FileParameterWidget(AbstractParameterWidget):
    '''
    A widget for opening a dialog for selecting a file.
    '''
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(self.add_field_widget)
    
    def add_field_widget(self, *args):
        w = FileFieldWidget()
        self.field = w
        self.ids['layout'].add_widget(w)
    
    def _get_parameter_value(self):
        return self.field.get_value()

class FloatSliderParameterWidget(AbstractParameterWidget):
    '''
    A widget for selecting a floating point number from a 
    '''
    def __init__(self, min=0, max=10, value=5, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(lambda *args: self.add_field_widget(min, max, value))
    
    def add_field_widget(self, min, max, value):
        w = Slider(min=min, max=max, value=value, step=0.1)
        self.field = w
        self.ids['layout'].add_widget(w)
    
    def _get_parameter_value(self):
        return self.field.value

class AccordionSlider(GridLayout):
    slider = ObjectProperty(None)
    param_label = StringProperty(None)
    param_value = NumericProperty(None)
    callback = ObjectProperty(None)
    def __init__(self, callback, *args, type='float', param_label='', min=0, 
                 max=100, value=50, **kwargs):
        super().__init__(**kwargs)
        self.param_label = param_label
        self.slider.min = min
        self.slider.max = max
        self.slider.step = (0.1 if type == 'float' else 1)
        self.callback = callback
    
    def on_slider_stop(self, slider, touch):
        if touch.grab_current is not None:
            self.callback.update_schema()

