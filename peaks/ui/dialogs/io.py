from kivy.properties import StringProperty

from .common import ParameterListDialog
from peaks.ui.parameters import *
from peaks.data.datasource import parse_csv

class SingleFileLoadDialog(ParameterListDialog):
    '''
    Dialog for loading a single delimited file from the file.
    '''
    title = StringProperty('Load delimited file...')
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

    @staticmethod
    def execute(app, parameters):
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
        app.post_data(data=spectrum)