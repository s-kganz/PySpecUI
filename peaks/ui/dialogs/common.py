from pubsub import pub
import os
from datetime import datetime

from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.properties import ObjectProperty, StringProperty
from kivy.clock import Clock
from kivy.event import EventDispatcher

class ParameterListDialog(Popup):
    '''
    Popup with a scroll view of classes derived from
    AbstractParameterWidget
    '''
    button_ok = ObjectProperty(None)
    errlabel = ObjectProperty(None)
    title = StringProperty('Display Title')

    def __init__(self, datasource, *args, **kwargs):
        self.ds = datasource
        self.parameters = dict()
        defaults = dict(
            size_hint = (None, None),
            size = (400, 600),
            auto_dismiss = False
        )
        defaults.update(**kwargs)
        super().__init__(*args, **defaults)
        self._build_content_area()
    
    def _build_content_area(self, *args):
        '''
        Add all of the user-defined parameters to the dialog
        content area.
        '''
        parameters = self.define_parameters()
        for widget in parameters:
            # add the widget to the popup
            self.ids['content_area'].add_widget(widget)
            if widget.param_name in self.parameters:
                print("[WARNING] Parameter named {} already exists.".format(widget.param_name))
            self.parameters[widget.param_name] = widget
    
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
        tr = ToolRun(self.ds, self, param_values)
        tr.start()
        self.dismiss()

    def define_parameters(self):
        '''
        Function that must be implemented by the user. Return a list of objects
        derived from AbstractParameterWidget.
        '''
        return []
    
    def execute(parameters):
        '''
        Function that implements tool execution. Parameters is a dictionary
        where keys are parameter name and values are parameter value.
        '''
        raise NotImplementedError("Tool execution must be defined.")

    def validate(self):
        '''
        Use the self.parameters object to access paramters as attributes, show error
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

class DisplayTextInput(TextInput):
    '''
    A text input that eats all user input.
    '''
    def insert_text(self, *args, **kwargs):
        return None
    
    def do_backspace(self, from_undo=False, mode='bkspc'):
        return None
    
    def delete_selection(self, from_undo=False):
        return None
    
    def cut(self, *args):
        return None

class ToolRunInfo(Popup):
    param_info = ObjectProperty(None)
    messages = ObjectProperty(None)
    start_time = ObjectProperty(None)
    end_time = ObjectProperty(None)

class ToolRun(EventDispatcher):
    '''
    Retain information about a particular tool execution's parameters
    and whether the execution was successful or not.
    '''
    status = StringProperty('')
    message_text = StringProperty('')
    start_time = ObjectProperty(None)
    finish_time = ObjectProperty(None)

    def __init__(self, ds, tool, parameters):
        self.Tool = type(tool)
        self.ds = ds
        self.name = tool.title
        self.parameters = parameters
        self.status = 'Not Started'
        del tool
    
    def start(self):
        pub.sendMessage('Data.StartThread', tool_run=self)
        self.status = 'Running'
        self.start_time = datetime.now()

    def finish(self):
        self.finish_time = datetime.now()

    def get_call(self):
        return lambda: self.Tool.execute(self, self.parameters)
    
    def post_data(self, data):
        pub.sendMessage('Data.Post', data=data)
    
    def append_status(self, message):
        self.message_text += message + '\n'
    
    def create_dialog(self):
        t = self.Tool(self.ds)
        for key in self.parameters:
            t.parameters[key].set_value(self.parameters[key])
        t.open()

    def create_info_dialog(self):
        tri = ToolRunInfo(title='Results of {}'.format(self.name))
        # Make start/end time labels
        start_text = 'Started at {}'.format(self.start_time.strftime('%H:%M:%S'))
        finish_text = '{} at {}'.format(self.status, self.finish_time.strftime('%H:%M:%S')) \
                      if self.status in ('Failed', 'Succeeded') else ''
        tri.start_time.text = start_text
        tri.end_time.text = finish_text
        # Make parameter text
        param_info_lines = [
            '{}:{}'.format(key, str(self.parameters[key])) for key in self.parameters
        ]
        tri.param_info.text = '\n'.join(param_info_lines)
        # Make message text
        tri.messages.text = self.message_text
        tri.open()
