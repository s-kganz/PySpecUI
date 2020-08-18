from .common import ParameterListDialog
from peaks.ui.parameters import *
from peaks.tools.transform import rescale, to_absorbance, to_transmittance

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
            SpectrumNameWidget(
                self.ds,
                default='absorbance',
                label_text='Output spectrum name:',
                param_name='name'
            )
        ]
    
    @staticmethod
    def execute(app, parameters):
        new_spec = parameters['spectrum'].apply_spec(
            to_absorbance
        )
        new_spec.name = parameters['name']
        
        app.post_data(data=new_spec)

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
            SpectrumNameWidget(
                self.ds,
                default='transmittance',
                label_text='Output spectrum name:',
                param_name='name'
            )
        ]
    
    @staticmethod
    def execute(app, parameters):
        new_spec = parameters['spectrum'].apply_spec(
            to_transmittance
        )
        new_spec.name = parameters['name']

        app.post_data(data=new_spec)

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
            SpectrumNameWidget(
                self.ds,
                default='rescaled',
                label_text='Output spectrum name:',
                param_name='name'
            )
        ]
    
    def validate(self):
        if not self.parameters['new_min'].get_value() < self.parameters['new_max'].get_value():
            self.show_error('New minimum must be strictly less than the new maximum.')
            return False
        return True

    @staticmethod
    def execute(app, parameters):
        new_spec = parameters['spectrum'].apply_spec(
            rescale,
            parameters['new_min'],
            parameters['new_max']
        )
        new_spec.name = parameters['name']
        app.post_data(data=new_spec)