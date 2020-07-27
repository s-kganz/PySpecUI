from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.slider import Slider
from kivy.properties import ObjectProperty, StringProperty
from kivy.factory import Factory
from kivy.uix.textinput import TextInput
from kivy.clock import Clock

import os
from pubsub import pub

from peaks.data.datasource import parse_csv
from peaks.data.models import ModelGauss
from peaks.ui.parameters import *
    
class ParameterNamespace(object):
    '''
    Helper object to hold parameter objects in the dialog.
    '''
    pass

class ParameterListDialog(Popup):
    '''
    Popup with a scroll view of classes derived from
    AbstractParameterWidget
    '''
    button_ok = ObjectProperty(None)
    
    def __init__(self, datasource, *args, **kwargs):
        self.ds = datasource
        self.ns = ParameterNamespace()
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
            setattr(self.ns, widget.param_name, widget)
    
    def _execute(self):
        '''
        Gather all parameter widgets from the content area and pass
        to execution function.
        '''
        param_values = {
            name:value for (name, value) in \
            map(lambda p: p.get_parameter_tuple(), self.ids['content_area'].children)
        }
        # Wrap the call in a lambda, start in own thread
        pub.sendMessage('Data.StartThread', caller=lambda: self.execute(param_values))

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

    def post_data(self, data):
        pub.sendMessage('Data.Post', data=data)

class LoadDialog(Popup):
    '''
    Dialog for selecting a file.
    '''
    callback = ObjectProperty(None)
    filechooser = ObjectProperty(None)

    def __init__(self, callback, *args, **kwargs):
        self.callback = callback
        defaults = dict(
            size_hint = (None, None),
            size = (600, 400),
            title = 'Select a file:',
            auto_dismiss = False
        )
        defaults.update(**kwargs)
        super().__init__(*args, **defaults)
    
    def post_result(self):
        try:
            f = self.filechooser.selection[0]
        except IndexError:
            f = ''
        path = os.path.join(self.filechooser.path, f)
        self.callback.text = path

class TestDialog(ParameterListDialog):
    '''
    Dialog that creates a parameter of each type in the application
    and prints the value associated with each parameter.
    '''
    def define_parameters(self):
        return [
            TextParameterWidget(
                label_text='Some text:',
                param_name='text'
            ),
            IntegerParameterWidget(
                label_text='An integer:',
                param_name='int'
            ),
            FloatParameterWidget(
                label_text='A float:',
                param_name='float'
            ),
            ChoiceParameterWidget(
                ['1', '2', '3'],
                label_text='A choice:',
                param_name='choice'
            ),
            FileParameterWidget(
                label_text='A file',
                param_name='file'
            ),
            SpectrumParameterWidget(
                self.ds,
                label_text='A spectrum',
                param_name='spectrum'
            ),
            FloatSliderParameterWidget(
                label_text='A float slider:',
                param_name='floating point slider'
            )
        ]
    
    def execute(self, parameters):
        for key in parameters:
            print("Parameter {:<10}: {}".format(key, parameters[key]))

class SingleFileLoadDialog(ParameterListDialog):
    '''
    Dialog for loading a single delimited file from the file.
    '''
    def define_parameters(self):
        return [
            FileParameterWidget(
                label_text="File to load:",
                param_name='file'
            ),
            ChoiceParameterWidget(
                ['Space', 'Comma', 'Tab'],
                label_text='Delimiter:',
                param_name='delimChoice',
                default=1
            ),
            IntegerParameterWidget(
                label_text='Frequency column index:',
                param_name='freqCol',
                default=0
            ),
            IntegerParameterWidget(
                label_text='Spectral column index:',
                param_name='specCol',
                default=1
            ),
            TextParameterWidget(
                label_text='Frequency unit:',
                param_name='freqUnit',
                default='x'
            ),
            TextParameterWidget(
                label_text='Spectral unit:',
                param_name='specUnit',
                default='y'
            ),
            TextParameterWidget(
                label_text='Comment character:',
                param_name='commentChar',
                default='#'
            ),
            IntegerParameterWidget(
                label_text='Lines to skip:',
                param_name='skipCount',
                default='0'
            )
        ]
    
    def execute(self, parameters):
        spectrum = parse_csv(
            delimChoice=parameters['delimChoice'],
            skipCount=parameters['skipCount'],
            freqCol=parameters['freqCol'],
            specCol=parameters['specCol'],
            commentChar=parameters['commentChar'],
            freqUnit=parameters['freqUnit'],
            specUnit=parameters['specUnit'],
            file=parameters['file']
        )
        self.post_data(data=spectrum)

class GaussModelDialog(ParameterListDialog):
    '''
    Dialog for creating a gaussian model of a spectrum.
    '''
    def define_parameters(self):
        return [
            SpectrumParameterWidget(
                self.ds,
                label_text='Spectrum to fit:',
                param_name='spectrum'
            ),
            IntegerParameterWidget(
                label_text='Minimum number of peaks:',
                param_name='peak_min'
            ),
            IntegerParameterWidget(
                label_text='Maximum number of peaks:',
                param_name='peak_max'
            ),
            IntegerParameterWidget(
                label_text="Savitsky-Golay polynomial order:",
                param_name='poly_order'
            ),
            TextParameterWidget(
                label_text='Model name:',
                param_name='model_name'
            )
        ]
    
    def execute(self, parameters):
        import time
        time.sleep(5)
        m = ModelGauss(parameters['spectrum'], None, name=parameters['model_name'])
        guess = m.guess_parameters(**parameters)
        try:
            assert(m.fit(guess))
        except AssertionError:
            raise RuntimeError("Model fitting failed.")
        self.post_data(data=m)

# Register dialogs in the factory
Factory.register('TestDialog', cls=TestDialog)
Factory.register('LoadDialog', cls=LoadDialog)
Factory.register('SingleFileLoadDialog', cls=SingleFileLoadDialog)
Factory.register('GaussModelDialog', cls=GaussModelDialog)