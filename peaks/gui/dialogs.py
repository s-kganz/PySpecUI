'''
Custom dialogs and dialog execution interface
'''
import os
from pubsub import pub

import wx
from wx.lib import sized_controls
from wx.lib.intctrl import IntCtrl

class CustomDialog(sized_controls.SizedDialog):
    '''
    Informal interface for all dialogs in this file. Provides utils
    for creating controls and dialog execution.
    '''
    def __init__(self, parent, title="Custom Dialog"):
        super(CustomDialog, self).__init__(parent, title=title)
        self.pane = self.GetContentsPane()
    
    def InitUI(self):
        '''
        Create UI controls, assigning to self as necessary
        to keep values available in self.Exec calls.
        '''  
        raise NotImplementedError("BuildUI must be defined!")

    def Exec(self):
        '''
        After the dialog has been filled out by the user, execute
        its function with pub.sendMessage calls.
        '''
        raise NotImplementedError("Exec must be implemented!")

    def AddOkCancel(self):
        '''
        Add Ok and Cancel buttons to the dialog. Call this last
        to put them at the bottom.
        '''
        # Final OK and cancel buttons
        btns_pane = sized_controls.SizedPanel(self.pane)
        btns_pane.SetSizerType('form')
        btns_pane.SetSizerProps(align="center")

        button_ok = wx.Button(btns_pane, wx.ID_OK, label='OK')
        button_ok.Bind(wx.EVT_BUTTON, self.OnButton)

        button_cancel = wx.Button(btns_pane, wx.ID_CANCEL, label='Cancel')
        button_cancel.Bind(wx.EVT_BUTTON, self.OnButton)

    def OnButton(self, event):
        '''
        Event handler for clicking Ok/Cancel buttons (or further bindings
        as set by the user).
        '''
        if self.IsModal():
            self.EndModal(event.EventObject.Id)
        else:
            self.Close()


class DialogLoad(CustomDialog):
    '''
    Dialog box for loading a data file.
    '''
    def __init__(self, parent, data):
        super(DialogLoad, self).__init__(parent, title="Load a delimited file...")
        
        opts = {
            'path': os.getcwd(),
        }
        opts.update(data)

        self.InitUI(opts['path'])

    def InitUI(self, path):

        file_pane = sized_controls.SizedPanel(self.pane)
        file_pane.SetSizerType('horizontal')
        file_pane.SetSizerProps(halign='left')

        # Add file selection control
        wx.StaticText(file_pane, label="File: ")
        self.fileCtrl = wx.FilePickerCtrl(file_pane, path=path)

        line1 = wx.StaticLine(self.pane, style=wx.LI_HORIZONTAL)
        line1.SetSizerProps(border=(('all', 5)), expand=True)

        # Add parse settings control
        parse_pane = sized_controls.SizedPanel(self.pane)
        parse_pane.SetSizerType('form')
        parse_pane.SetSizerProps(halign="left")

        # Delimiter choice
        wx.StaticText(parse_pane, label="Delimiter: ")
        self.delimCtrl = wx.Choice(
            parse_pane, choices=["Tab", "Comma", "Space"])
        self.delimCtrl.SetSelection(1)

        # Header choice
        wx.StaticText(parse_pane, label="Parse headers: ")
        self.headCtrl = wx.CheckBox(parse_pane)

        # Comment character
        wx.StaticText(parse_pane, label="Comment character: ")
        self.commCtrl = wx.TextCtrl(parse_pane, value='#')
        self.commCtrl.SetMaxLength(1)

        # Frequency column
        wx.StaticText(parse_pane, label="Index of frequency column: ")
        self.freqIndCtrl = IntCtrl(
            parse_pane, min=0, limited=True, allow_none=False)

        # Lines to skip
        wx.StaticText(parse_pane, label="Lines to skip: ")
        self.skipCtrl = IntCtrl(
            parse_pane, min=0, limited=True, allow_none=False)

        # Second separating line
        line2 = wx.StaticLine(self.pane, style=wx.LI_HORIZONTAL)
        line2.SetSizerProps(border=(('all', 5)), expand=True)

        # Metadata settings control
        meta_pane = sized_controls.SizedPanel(self.pane)
        meta_pane.SetSizerType('form')
        meta_pane.SetSizerProps(halign="left")

        wx.StaticText(meta_pane, label="Frequency unit: ")
        self.freqUnitCtrl = wx.TextCtrl(meta_pane, value='x')

        wx.StaticText(meta_pane, label="Spectral unit: ")
        self.specUnitCtrl = wx.TextCtrl(meta_pane, value='y')

        # Third separating line
        line3 = wx.StaticLine(self.pane, style=wx.LI_HORIZONTAL)
        line3.SetSizerProps(border=(('all', 5)), expand=True)

        self.AddOkCancel()

        self.Fit()

    def Exec(self):
        '''
        Execute the load tool
        '''
        # Package all the parameters into a dictionary and
        # send to the data manager.
        file = self.fileCtrl.GetPath()
        delimStr = self.delimCtrl.GetString(
                self.delimCtrl.GetSelection())
        commChar = self.commCtrl.GetValue()
        options = {
                'delimChoice': delimStr,
                'header': self.headCtrl.GetValue(),
                'commentChar': commChar,
                'freqColInd': self.freqIndCtrl.GetValue(),
                'skipCount': self.skipCtrl.GetValue(),
                'freqUnit': self.freqUnitCtrl.GetValue(),
                'specUnit': self.specUnitCtrl.GetValue()
            }
        
        pub.sendMessage('Data.LoadCSV', file=file, options=options)

class DialogGaussModel(CustomDialog):
    '''
    Dialog for fitting a Gaussian model to a spectrum.
    '''
    def __init__(self, parent, data):
        '''
        The initializer must receive a dictionary of (name, id) key/value pairs
        where name is the choice displayed in the dialog, and the id is available
        to retrieve the spectrum from the datamanager.
        '''
        super(DialogGaussModel, self).__init__(parent, title='Fit Gaussian peaks...')
        
        opts = {
            'traces' : [],
            'datasrc' : None
        }
        opts.update(data)

        self.datasrc = opts['datasrc']
        
        self.InitUI(opts['traces'])

    def InitUI(self, traces):
        spec_pane = sized_controls.SizedPanel(self.pane)
        spec_pane.SetSizerType('horizontal')
        spec_pane.SetSizerProps(halign='left')

        # Top section: pick the spectrum
        wx.StaticText(spec_pane, label="Spectrum to fit:")
        trace_names = list(traces.keys())
        self.ctrl_spec_name = wx.Choice(
            spec_pane, 
            choices=trace_names)
        self.ctrl_spec_name.SetSelection(0)
        
        line = wx.StaticLine(self.pane, style=wx.LI_HORIZONTAL)
        line.SetSizerProps(border=(('all', 5)), expand=True)

        model_pane = sized_controls.SizedPanel(self.pane)
        model_pane.SetSizerType('form')
        model_pane.SetSizerProps(halign="left")

        # Bottom: fitting parameters
        wx.StaticText(model_pane, label="Minimum number of peaks to fit:")
        self.ctrl_min_peaks = IntCtrl(
            model_pane, min=0, value=0, allow_none=False
        )
        wx.StaticText(model_pane, label="Maximum number of peaks to fit:")
        self.ctrl_max_peaks = IntCtrl(
            model_pane, min=1, value=5, allow_none=False
        )
        wx.StaticText(model_pane, label="Savitsky-Golay polynomial order:")
        self.ctrl_poly_order = IntCtrl(
            model_pane, min=1, value=2, allow_none=False
        )
        # TODO give the user a way to specify the window length
        # An integer input needs to be validated as odd, greater than the polynomial
        # order, but less than the length of the frequency domain. One option is to
        # specify the nearest odd integer to some fraction of the frequency domain 
        # length, but this is not trivial to implement in wxpython.

        self.AddOkCancel()

        self.Fit()
    
    def Exec(self):
        '''
        Execute Gaussian fitting.
        '''
        print("Exec!")
        pass

def ExecDialog(D, data=None):
    '''
    Instantiate the passed dialog type, show it to the user, and execute
    if the user fills out the dialog.

    D must be a type. data is optional - 
    '''
    with D(None, data) as dialog:
        if dialog.ShowModal() == wx.ID_CANCEL:
            # User changed their mind
            return

        dialog.Exec()
        
pub.subscribe(ExecDialog, 'Dialog.Run')
