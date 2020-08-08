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
from peaks.data.spectrum import Spectrum
from peaks.ui.parameters import *
from peaks.tools.detrend import polynomial_detrend
from peaks.tools.transform import to_absorbance, to_transmittance, rescale
    
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
    errlabel = ObjectProperty(None)

    def __init__(self, datasource, *args, **kwargs):
        self.ds = datasource
        self.parameters = ParameterNamespace()
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
            setattr(self.parameters, widget.param_name, widget)
    
    def _execute(self):
        '''
        Gather all parameter widgets from the content area and pass
        to execution function.
        '''
        if not self.validate(): return
        param_values = {
            name:value for (name, value) in \
            map(lambda p: p.get_parameter_tuple(), self.ids['content_area'].children)
        }
        # Wrap the call in a lambda, start in own thread
        pub.sendMessage('Data.StartThread', caller=lambda: self.execute(param_values))
        # Finally, close the dialog
        self.dismiss()

    def define_parameters(self):
        '''
        Function that must be implemented by the user. Return a list of objects
        derived from AbstractParameterWidget.
        '''
        return []
    
    def execute(self, parameters):
        '''
        Function that implements tool execution. Parameters is a dictionary
        where keys are parameter name and values are parameter value.
        '''
        raise NotImplementedError("Tool execution must be defined.")

    def validate(self):
        '''
        Use the self.ns object to access paramters as attributes, show error
        text as necessary
        '''
        return True
    
    def show_error(self, text):
        self.errlabel.text = text

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
                label_text="Savitsky-Golay polynomial degree:",
                param_name='poly_order'
            ),
            TextParameterWidget(
                label_text='Model name:',
                param_name='model_name',
                default='gauss'
            )
        ]
    
    def execute(self, parameters):
        m = ModelGauss(parameters['spectrum'], None, name=parameters['model_name'])
        guess = m.guess_parameters(**parameters)
        try:
            assert(m.fit(guess))
        except AssertionError:
            raise RuntimeError("Model fitting failed.")
        self.post_data(data=m)
    
    def validate(self):
        # Validate savgol polynomial degree
        if not self.parameters.poly_order.get_value() > 0:
            self.show_error('Sav-Gol polynomial must have degree greater than zero.')
            return False
        
        # Validate peak min/max value
        peak_min = self.parameters.peak_min.get_value()
        peak_max = self.parameters.peak_max.get_value()
        if any(x < 0 for x in (peak_min, peak_max)):
            self.show_error('Peak min and max must be greater than or equal to zero.')
            return False
        
        # Validate that min < max
        if peak_min > peak_max:
            self.show_error('Peak min must be less than or equal to peak max.')
            return False
        
        return True

class PolynomialBaselineDialog(ParameterListDialog):
    '''
    Dialog for removing a simple polynomial baseline from a dialog.
    '''
    def define_parameters(self):
        return [
            SpectrumParameterWidget(
                self.ds,
                label_text='Spectrum to fit:',
                param_name='spectrum'
            ),
            IntegerParameterWidget(
                default=1, 
                label_text='Baseline degreee:',
                param_name='degree'
            ),
            #TODO create range slider widget to replace these
            IntegerParameterWidget(
                default=0,
                label_text='Lower bound of baseline region:',
                param_name='lower_bound'
            ),
            IntegerParameterWidget(
                default=0,
                label_text='Upper bound of baseline region:',
                param_name='upper_bound'
            ),
            CheckBoxParameterWidget(
                default=False,
                label_text='Invert baseline region:',
                param_name='invert'
            ),
            TextParameterWidget(
                default='detrended',
                label_text='Output spectrum name:',
                param_name='name'
            )
        ]
    
    def execute(self, parameters):
        new_spec = parameters['spectrum'].apply_spec_freq(
            polynomial_detrend,
            parameters['lower_bound'],
            parameters['upper_bound'],
            parameters['degree'],
            invert=parameters['invert']
        )
        new_spec.name = parameters['name']

        self.post_data(data=new_spec)
    
    def validate(self):
        # Degree must be greater than zero
        if not self.parameters.degree.get_value() > 0:
            self.show_error('Baseline degree must be greater than zero.')
            return False
        
        # Lower/upper bounds must be ordered right
        if not self.parameters.lower_bound.get_value() <= self.parameters.upper_bound.get_value():
            self.show_error('Upper bound of baseline must be greater than the lower bound.')
            return False

        return True

class ToAbsorbanceDialog(ParameterListDialog):
    '''
    Dialog for converting a transmittance spectrum to an absorbance spectrum.
    '''
    def define_parameters(self):
        return [
            SpectrumParameterWidget(
                self.ds,
                label_text='Spectrum to transform:',
                param_name='spectrum'
            ),
            TextParameterWidget(
                default='absorbance',
                label_text='Output spectrum name:',
                param_name='name'
            )
        ]
    
    def execute(self, parameters):
        new_spec = parameters['spectrum'].apply_spec(
            to_absorbance
        )
        
        self.post_data(data=new_spec)

class ToTransmittanceDialog(ParameterListDialog):
    '''
    Dialog for converting a transmittance spectrum to an absorbance spectrum.
    '''
    def define_parameters(self):
        return [
            SpectrumParameterWidget(
                self.ds,
                label_text='Spectrum to transform:',
                param_name='spectrum'
            ),
            TextParameterWidget(
                default='transmittance',
                label_text='Output spectrum name:',
                param_name='name'
            )
        ]
    
    def execute(self, parameters):
        new_spec = parameters['spectrum'].apply_spec(
            to_transmittance
        )

        self.post_data(data=new_spec)

class RescaleDialog(ParameterListDialog):
    '''
    Dialog for converting a transmittance spectrum to an absorbance spectrum.
    '''
    def define_parameters(self):
        return [
            SpectrumParameterWidget(
                self.ds,
                label_text='Spectrum to transform:',
                param_name='spectrum'
            ),
            FloatParameterWidget(
                default=0.0,
                label_text='Minimum value:',
                param_name='new_min'
            ),
            FloatParameterWidget(
                default=1.0,
                label_text='Maximum value:',
                param_name='new_max'
            ),
            TextParameterWidget(
                default='rescaled',
                label_text='Output spectrum name:',
                param_name='name'
            )
        ]
    
    def validate(self):
        if not self.parameters.new_min.get_value() < self.parameters.new_max.get_value():
            self.show_error('New minimum must be strictly less than the new maximum.')
            return False
        return True

    def execute(self, parameters):
        new_spec = parameters['spectrum'].apply_spec(
            rescale,
            parameters['new_min'],
            parameters['new_max']
        )
        new_spec.name = parameters['name']
        self.post_data(data=new_spec)

# Register dialogs in the factory
Factory.register('TestDialog', cls=TestDialog)
Factory.register('LoadDialog', cls=LoadDialog)
Factory.register('SingleFileLoadDialog', cls=SingleFileLoadDialog)
Factory.register('GaussModelDialog', cls=GaussModelDialog)
Factory.register('PolynomialBaselineDialog', cls=PolynomialBaselineDialog)
Factory.register('ToAbsorbanceDialog', cls=ToAbsorbanceDialog)
Factory.register('ToTransmittanceDialog', cls=ToTransmittanceDialog)
Factory.register('RescaleDialog', cls=RescaleDialog)