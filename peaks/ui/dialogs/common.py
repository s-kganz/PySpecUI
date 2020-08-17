from pubsub import pub
import os

from kivy.uix.popup import Popup
from kivy.properties import ObjectProperty
from kivy.clock import Clock

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
        tr = ToolRun(self.ds, type(self), param_values)
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

class ToolRun(object):
    '''
    Retain information about a particular tool execution's parameters
    and whether the execution was successful or not.
    '''
    def __init__(self, ds, tool, parameters):
        self.Tool = tool
        self.ds = ds
        self.parameters = parameters
        self.status_text = ""
        self.status = None
    
    def start(self):
        pub.sendMessage('Data.StartThread', tool_run=self)
        self.status = 'running'

    def get_call(self):
        return lambda: self.Tool.execute(self, self.parameters)
    
    def post_data(self, data):
        pub.sendMessage('Data.Post', data=data)
    
    def append_status(self, message):
        self.status_text += "\n" + message
    
    def create_dialog(self):
        t = self.Tool(ds, title='A tool')
