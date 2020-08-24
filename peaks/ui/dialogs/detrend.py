from kivy.properties import StringProperty

from .common import ParameterListDialog
from peaks.ui.parameters import *
from peaks.tools.detrend import (
    polynomial_detrend,
    boxcar_smooth, 
    triangular_smooth, 
    gaussian_smooth,
    savgol_filter,
    rolling_ball
)

class BoxcarSmoothDialog(ParameterListDialog):
    '''
    Dialog for generating a spectrum smoothed by a moving
    average.
    '''
    title = StringProperty('Boxcar filter...')
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
            SpectrumNameWidget(
                self.ds,
                default='smoothed_boxcar',
                label_text='Output spectrum name:',
                param_name='output_name'
            )
        ]
    
    def validate(self):
        if self.parameters['winlen'].get_value() <= 0:
            self.show_error('Window length must be greater than zero.')
            return False
        
        return True
    
    @staticmethod
    def execute(app, parameters):
        new_spec = parameters['spectrum'].apply_spec(
            boxcar_smooth,
            parameters['winlen']
        )
        new_spec.name = parameters['output_name']

        app.post_data(data=new_spec)

class TriangleSmoothDialog(ParameterListDialog):
    '''
    Dialog for generating a spectrum smoothed by convolution
    with a triangular window.
    '''
    title = StringProperty('Triangular filter...')
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
            SpectrumNameWidget(
                self.ds,
                default='smoothed_triangular',
                label_text='Output spectrum name:',
                param_name='output_name'
            )
        ]
    
    def validate(self):
        if self.parameters['winlen'].get_value() <= 0:
            self.show_error('Window length must be greater than zero.')
            return False
        
        return True
    
    @staticmethod
    def execute(app, parameters):
        new_spec = parameters['spectrum'].apply_spec(
            triangular_smooth,
            parameters['winlen']
        )
        new_spec.name = parameters['output_name']

        app.post_data(data=new_spec)

class GaussianSmoothDialog(ParameterListDialog):
    '''
    Dialog for generating a spectrum smoothed by convolution
    with a Gaussian window.
    '''
    title = StringProperty('Gaussian filter...')
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
            FloatParameterWidget(
                default=1.0,
                label_text='Shape parameter:',
                param_name='shape'
            ),
            FloatParameterWidget(
                default=1.0,
                label_text='Peak width:',
                param_name='sigma'
            ),
            SpectrumNameWidget(
                self.ds,
                default='smoothed_gaussian',
                label_text='Output spectrum name:',
                param_name='output_name'
            )
        ]
    
    def validate(self):
        if self.parameters['winlen'].get_value() <= 0:
            self.show_error('Window length must be greater than zero.')
            return False
        
        return True
    
    @staticmethod
    def execute(app, parameters):
        new_spec = parameters['spectrum'].apply_spec(
            gaussian_smooth,
            parameters['winlen'],
            parameters['shape'],
            parameters['sigma']
        )
        new_spec.name = parameters['output_name']

        app.post_data(data=new_spec)

class SavgolSmoothDialog(ParameterListDialog):
    '''
    Dialog for generating a spectrum smoothed by convolution
    with a Gaussian window.
    '''
    title = StringProperty('Savitsky-Golay filter...')
    def define_parameters(self):
        return [
            SpectrumParameterWidget(
                self.ds,
                label_text='Spectrum to smooth:',
                param_name='spectrum'
            ),
            IntegerParameterWidget(
                default=11,
                label_text='Window length (in points):',
                param_name='winlen'
            ),
            IntegerParameterWidget(
                default=1,
                label_text='Polynomial Order:',
                param_name='polyorder'
            ),
            SpectrumNameWidget(
                self.ds,
                default='smoothed_savgol',
                label_text='Output spectrum name:',
                param_name='output_name'
            )
        ]
    
    def validate(self):
        if self.parameters['winlen'].get_value() <= 0:
            self.show_error('Window length must be greater than zero.')
            return False
        if not self.parameters['winlen'].get_value() % 2:
            self.show_error('Window length must be odd.')
            return False
        if not self.parameters['polyorder'].get_value() >= 0:
            self.show_error('Polynomial order must be greater than zero.')
            return False
        
        return True
    
    @staticmethod
    def execute(app, parameters):
        new_spec = parameters['spectrum'].apply_spec(
            savgol_filter,
            parameters['winlen'],
            parameters['polyorder']
        )
        new_spec.name = parameters['output_name']

        app.post_data(data=new_spec)

class PolynomialBaselineDialog(ParameterListDialog):
    '''
    Dialog for removing a simple polynomial baseline from a dialog.
    '''
    title = StringProperty('Polynomial detrend...')
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
            SpectrumNameWidget(
                self.ds,
                default='detrended',
                label_text='Output spectrum name:',
                param_name='name'
            )
        ]
    
    @staticmethod
    def execute(app, parameters):
        new_spec = parameters['spectrum'].apply_spec_freq(
            polynomial_detrend,
            parameters['lower_bound'],
            parameters['upper_bound'],
            parameters['degree'],
            invert=parameters['invert']
        )
        new_spec.name = parameters['name']

        app.post_data(data=new_spec)
    
    def validate(self):
        # Degree must be greater than zero
        if not self.parameters['degree'].get_value() > 0:
            self.show_error('Baseline degree must be greater than zero.')
            return False
        
        # Lower/upper bounds must be ordered right
        if not self.parameters['lower_bound'].get_value() <= self.parameters['upper_bound'].get_value():
            self.show_error('Upper bound of baseline must be greater than the lower bound.')
            return False

        return True

class RollingBallDialog(ParameterListDialog):
    '''
    Dialog for applying the rolling ball smoothing algorithm
    to a spectrum.
    '''
    title = StringProperty('Rolling Ball filter...')
    def define_parameters(self):
        return [
           SpectrumParameterWidget(
                self.ds,
                label_text='Spectrum to detrend:',
                param_name='spectrum'
            ),
            IntegerParameterWidget(
                default=15, 
                label_text='Min/max window length:',
                param_name='minmax_winlen'
            ),
            IntegerParameterWidget(
                default=15,
                label_text='Smoothing window length:',
                param_name='smooth_winlen'
            ),
            SpectrumNameWidget(
                self.ds,
                default='rolling_ball',
                label_text='Output spectrum name:',
                param_name='out_name'
            )
        ]
    
    @staticmethod
    def execute(app, parameters):
        new_spec = parameters['spectrum'].apply_spec(
            rolling_ball,
            parameters['minmax_winlen'],
            parameters['smooth_winlen'],
        )
        new_spec.name = parameters['out_name']

        app.post_data(data=new_spec)
    
    def validate(self):
        # Both windows must be greater than zero.
        if self.parameters['minmax_winlen'].get_value() <= 0 or\
           self.parameters['smooth_winlen'].get_value() <= 0:
            self.show_error('Both window lengths must be greater than zero.')
            return False

        return True