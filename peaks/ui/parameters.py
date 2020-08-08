from kivy.properties import ObjectProperty, StringProperty, NumericProperty
from kivy.clock import Clock
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.slider import Slider
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.checkbox import CheckBox

from numpy import around
from os.path import expanduser

__all__ = ['IntegerParameterWidget', 'FloatParameterWidget', 'TextParameterWidget',
           'ChoiceParameterWidget', 'SpectrumParameterWidget', 'FileParameterWidget',
           'FloatSliderParameterWidget', 'AccordionSlider', 'CheckBoxParameterWidget']

class AbstractParameterWidget(BoxLayout):
    '''
    Abstract parameter widget defining the interface
    that all other widgets must adhere to.
    '''
    field = ObjectProperty(None)
    def __init__(self, label_text='', param_name='', default=None, **kwargs):
        self.label_text = label_text
        self.param_name = param_name
        super().__init__(**kwargs)

    def get_parameter_tuple(self):
        return self.param_name, self.get_value()

    def get_value(self):
        raise NotImplementedError("Parameter must define get_value()")

    def set_value(self):
        raise NotImplementedError('Paramter must define set_value()')

class TextParameterWidget(AbstractParameterWidget):
    '''
    A general text input.
    '''
    def __init__(self, default='', on_change=None, **kwargs):
        super().__init__(**kwargs)
        w = TextInput(
            multiline = False,
            text=default
        )
        if callable(on_change): w.bind(text = on_change)
        self.field = w
        self.ids['layout'].add_widget(w)

    def get_value(self):
        return self.field.text
    
    def set_value(self, new):
        self.field.text = new

class IntegerParameterWidget(TextParameterWidget):
    '''
    A text field allowing numeric characters only.
    '''
    def __init__(self, *args, default=0, on_change=None, **kwargs):
        super().__init__(default=str(default), on_change=on_change, **kwargs)
        self.field.input_filter = 'int'
    
    def get_value(self):
        return int(self.field.text) if len(self.field.text) > 0 else None
    
    def set_value(self, new):
        self.field.text = str(new)

class FloatParameterWidget(TextParameterWidget):
    '''
    A text field allowing numeric input and one decimal point.
    '''
    def __init__(self, default=0, on_change=None, **kwargs):
        super().__init__(default=str(default), on_change=on_change, **kwargs)
        self.field.input_filter = 'float'
    
    def get_value(self):
        return float(self.field.text) if len(self.field.text) > 0 else None
    
    def set_value(self, new):
        self.field.text = str(new)

class ChoiceParameterWidget(AbstractParameterWidget):
    '''
    A widget for a dropdown menu of choices.
    '''
    def __init__(self, choices, default=0, on_change=None, **kwargs):
        # Default is the index of the choice to use
        self.choices = choices
        super().__init__(**kwargs)

        # Boundary checking
        default = max(0, min(default, len(self.choices)))
        w = Spinner(
            text = self.choices[default],
            values = self.choices.copy()
        )
        if callable(on_change): w.bind(text=on_change)
        self.field = w
        self.ids['layout'].add_widget(w)
        del self.choices

    def get_value(self):
        return self.field.text
    
    def set_value(self, new):
        if new in self.field.values:
            self.field.text = new

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
    
    def get_value(self):
        return self.choice_dict[self.field.text]
    
    def set_value(self, new):
        print('[WARNING] [SpectrumParameterWidget] Setting the value of this widget'
              'is not supported.')

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
    
    def set_value(self, new):
        self.text_field.text = new


class FileParameterWidget(AbstractParameterWidget):
    '''
    A widget for opening a dialog for selecting a file. The default
    is the user's home directory.
    '''
    def __init__(self, default=expanduser('~'), on_change=None, **kwargs):
        super().__init__(**kwargs)
    
        w = FileFieldWidget()
        if callable(on_change): w.text_field.bind(text=on_change)
        self.field = w
        self.ids['layout'].add_widget(w)
        self.set_value(default)
    
    def get_value(self):
        return self.field.get_value()
    
    def set_value(self, new):
        self.field.set_value(new)

class FloatSliderParameterWidget(AbstractParameterWidget):
    '''
    A widget for selecting a floating point number from a 
    '''
    def __init__(self, min=0, max=10, value=5, on_change=None, **kwargs):
        super().__init__(**kwargs)
    
        w = Slider(min=min, max=max, value=value, step=0.1)
        if callable(on_change): w.bind(value = on_change)
        self.field = w
        self.ids['layout'].add_widget(w)
    
    def get_value(self):
        return self.field.value
    
    def set_value(self, min=None, max=None, value=None):
        if min is not None: self.field.min = min
        if max is not None: self.field.max = max
        if value is not None: self.field.value = value

class CheckBoxParameterWidget(AbstractParameterWidget):
    def __init__(self, value=True, on_change=None, **kwargs):
        super().__init__(**kwargs)

        w = CheckBox(active=value)
        if callable(on_change): w.bind(active=on_change)
        self.field = w
        self.ids['layout'].add_widget(w)
    
    def get_value(self):
        return self.field.active
    
    def set_value(self, new):
        self.field.active = new


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
        self.slider.value = float(around(value, decimals=1))
        self.callback = callback
    
    def on_slider_stop(self, slider, touch):
        if touch.grab_current is not None:
            self.callback.update_schema()

