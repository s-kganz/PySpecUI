from .common import ParameterListDialog
from peaks.ui.parameters import *
from peaks.data.models import ModelGauss

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
                param_name='poly_order',
                default=2
            ),
            SpectrumNameWidget(
                self.ds,
                label_text='Model name:',
                param_name='model_name',
                default='gauss'
            )
        ]
    
    @staticmethod
    def execute(app, parameters):
        m = ModelGauss(parameters['spectrum'], None, name=parameters['model_name'])
        guess = m.guess_parameters(**parameters)
        try:
            assert(m.fit(guess))
        except AssertionError:
            raise RuntimeError("Model fitting failed.")
        m.name = 'gauss'
        app.post_data(data=m)
    
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