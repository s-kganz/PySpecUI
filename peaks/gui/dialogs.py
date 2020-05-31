'''
Custom dialogs
'''
import os

import wx
from wx.lib import sized_controls
from wx.lib.intctrl import IntCtrl

class DialogLoad(sized_controls.SizedDialog):
    '''
    Dialog box for loading a data file.
    '''
    def __init__(self, parent, path=os.getcwd(), title="Load a file"):
        super(DialogLoad, self).__init__(parent, title=title)
        self.pane = self.GetContentsPane()
        self.InitUI(path=path)

    def InitUI(self, path=os.getcwd()):

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

        # Final OK and cancel buttons
        btns_pane = sized_controls.SizedPanel(self.pane)
        btns_pane.SetSizerType('form')
        btns_pane.SetSizerProps(align="center")

        button_ok = wx.Button(btns_pane, wx.ID_OK, label='OK')
        button_ok.Bind(wx.EVT_BUTTON, self.on_button)

        button_cancel = wx.Button(btns_pane, wx.ID_CANCEL, label='Cancel')
        button_cancel.Bind(wx.EVT_BUTTON, self.on_button)

        self.Fit()

    def on_button(self, event):
        if self.IsModal():
            self.EndModal(event.EventObject.Id)
        else:
            self.Close()

class DialogGaussModel(sized_controls.SizedDialog):
    '''
    Dialog for fitting a Gaussian model to a spectrum.
    '''
    def __init__(self, parent, traces, title="Fit Gaussian peaks"):
        '''
        The initializer must receive a dictionary of (name, id) key/value pairs
        where name is the choice displayed in the dialog, and the id is available
        to retrieve the spectrum from the datamanager.
        '''
        super(DialogGaussModel, self).__init__(parent, title=title)
        self.pane = self.GetContentsPane()
        self.InitUI(traces)

    def InitUI(self, traces):
        spec_pane = sized_controls.SizedPanel(self.pane)
        spec_pane.SetSizerType('horizontal')
        spec_pane.SetSizerProps(halign='left')

        # Top section: pick the spectrum
        wx.StaticText(spec_pane, label="Spectrum to fit:")
        trace_names = list(traces.keys())
        self.ctrl_spec_name = wx.ListBox(
            spec_pane, 
            choices=trace_names, 
            style=wx.LB_SINGLE)
        
        line = wx.StaticLine(self.pane, style=wx.LI_HORIZONTAL)
        line.SetSizerProps(border=(('all', 5)), expand=True)

        model_pane = sized_controls.SizedPanel(self.pane)
        model_pane.SetSizerType('form')
        model_pane.SetSizerProps(halign="left")

        # Bottom: fitting parameters
        wx.StaticText(model_pane, label="Minimum number of peaks to fit:")
        self.ctrl_min_peaks = IntCtrl(
            model_pane, min=0, value=None, allow_none=True
        )
        wx.StaticText(model_pane, label="Maximum number of peaks to fit:")
        self.ctrl_max_peaks = IntCtrl(
            model_pane, min=1, value=None, allow_none=True
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

        # Final OK and cancel buttons
        btns_pane = sized_controls.SizedPanel(self.pane)
        btns_pane.SetSizerType('form')
        btns_pane.SetSizerProps(align="center")

        button_ok = wx.Button(btns_pane, wx.ID_OK, label='OK')
        button_ok.Bind(wx.EVT_BUTTON, self.on_button)

        button_cancel = wx.Button(btns_pane, wx.ID_CANCEL, label='Cancel')
        button_cancel.Bind(wx.EVT_BUTTON, self.on_button)

        self.Fit()

    def on_button(self, event):
        if self.IsModal():
            self.EndModal(event.EventObject.Id)
        else:
            self.Close()