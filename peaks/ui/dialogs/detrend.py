from .common import ParameterListDialog
from peaks.ui.parameters import *
from peaks.tools.detrend import polynomial_detrend

class BoxcarSmoothDialog(ParameterListDialog):
    '''
    Dialog for generating a spectrum smoothed by a moving
    average.
    '''
    def define_parameters(self):
        return [
            SpectrumParameterWidget(
                self.ds,
                label_text='Spectrum to smooth:',
                param_name='spectrum'
            ),
            IntegerParameterWidget(
                default=10,
                label_text='Window length (in points):',
                param_name='winlen'
            ),
            TextParameterWidget(
                default='smoothed',
                label_text='Output spectrum name:',
                param_name='output_name'
            )
        ]
    
    def validate(self):
        if self.parameters.winlen.get_value() <= 0:
            self.show_error('Window length must be greater than zero.')
            return False
        
        return True
    
    def execute(self, parameters):
        

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