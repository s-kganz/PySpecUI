'''
This file includes implementation of derived classes for building
the application interface.
'''

import wx
from wx.lib.intctrl import IntCtrl
from wx.lib import sized_controls
from wxasync import AsyncBind, WxAsyncApp, StartCoroutine
from wxmplot import PlotPanel

import time
import os
import asyncio

class LoadDialog(sized_controls.SizedDialog):

    def __init__(self, *args, **kwargs):
        super(LoadDialog, self).__init__(*args, **kwargs)
        self.pane = self.GetContentsPane()
        self.InitUI()
    
    def InitUI(self):
        file_pane = sized_controls.SizedPanel(self.pane)
        file_pane.SetSizerType('horizontal')
        file_pane.SetSizerProps(halign='left')

        # Add file selection control
        wx.StaticText(file_pane, label="File: ")
        self.fileCtrl = wx.FilePickerCtrl(file_pane)

        line1 = wx.StaticLine(self.pane, style=wx.LI_HORIZONTAL)
        line1.SetSizerProps(border=(('all', 5)), expand=True)

        # Add parse settings control
        parse_pane = sized_controls.SizedPanel(self.pane)
        parse_pane.SetSizerType('form')
        parse_pane.SetSizerProps(halign="left")
        
        # Delimiter choice
        wx.StaticText(parse_pane, label="Delimiter: ")
        self.delimCtrl = wx.Choice(parse_pane, choices=["Tab", "Comma", "Space"])

        # Header choice
        wx.StaticText(parse_pane, label="Parse headers: ")
        self.headCtrl = wx.CheckBox(parse_pane)

        # Comment character
        wx.StaticText(parse_pane, label="Comment character: ")
        self.commCtrl = wx.TextCtrl(parse_pane)
        self.commCtrl.SetMaxLength(1)

        # Frequency column
        wx.StaticText(parse_pane, label="Index of frequency column: ")
        self.freqIndCtrl = IntCtrl(parse_pane, min=0, limited=True, allow_none=False)

        # Lines to skip
        wx.StaticText(parse_pane, label="Lines to skip: ")
        self.skipCtrl = IntCtrl(parse_pane, min=0, limited=True, allow_none=False)

        # Second separating line
        line2 = wx.StaticLine(self.pane, style=wx.LI_HORIZONTAL)
        line2.SetSizerProps(border=(('all', 5)), expand=True)

        # Metadata settings control
        meta_pane= sized_controls.SizedPanel(self.pane)
        meta_pane.SetSizerType('form')
        meta_pane.SetSizerProps(halign="left")
        
        wx.StaticText(meta_pane, label="Frequency unit: ")
        self.freqUnitCtrl = wx.TextCtrl(meta_pane)

        wx.StaticText(meta_pane, label="Spectral unit: ")
        self.specUnitCtrl = wx.TextCtrl(meta_pane)

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

class SubPanel(wx.Panel):
    '''
    Superclass for panels in the application that implement their own widgets. Derived
    classes implement InitUI and other functions.
    '''

    def __init__(self, parent, datasrc):
        '''
        Initializer for the SubPanel class. Parent must be a pointer
        to either a panel or a window.
        '''
        super(SubPanel, self).__init__()
        self.parent = parent
        self.panel = wx.Panel(self.parent)
        self.datasrc = datasrc
        self.InitUI()

    def InitUI(self):
        '''
        Unimplemented functions as a placeholder for custom widgets
        defined by derived classes.
        '''
        pass

    def GetPanel(self):
        '''
        Return a pointer to the panel (i.e. the widget container) for this
        SubPanel.
        '''
        return self.panel


class TabPanel(SubPanel):
    '''
    Class implementing a notebook-style collection of panels.
    '''

    def __init__(self, parent, datasrc, ntabs=4):
        self.ntabs = ntabs
        super(TabPanel, self).__init__(parent, datasrc)

    def InitUI(self):
        '''
        Initialize self.ntabs panels
        '''
        # Create notebook object
        nb = wx.Notebook(self.panel)
        # Create tab objects
        tabs = []
        for i in range(self.ntabs):
            p = wx.Panel(nb)
            txt = wx.StaticText(p, label="Tab {}".format(i+1))
            tabs.append(p)

        # Create notebook object
        for i in range(len(tabs)):
            nb.AddPage(tabs[i], "Tab {}".format(i+1))

        # Place notebook in a sizer so it expands to the size of the panel
        sizer = wx.BoxSizer()
        sizer.Add(nb, 1, wx.EXPAND)

        self.panel.SetSizer(sizer)


class TextPanel(SubPanel):
    def __init__(self, parent, datasrc, text=wx.EmptyString):
        self.text = text
        super(TextPanel, self).__init__(parent, datasrc)

    def InitUI(self):
        txt = wx.StaticText(self.panel, label=self.text)

        # Create BoxSizers to center static text
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(txt, 0, wx.CENTER)

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add((0, 0), 1, wx.EXPAND)
        vbox.Add(hbox, 0, wx.CENTER)
        vbox.Add((0, 0), 1, wx.EXPAND)

        self.panel.SetSizer(vbox)


class PlotRegion(SubPanel):
    def __init__(self, parent, datasrc):
        super(PlotRegion, self).__init__(parent, datasrc)

    def InitUI(self):
        self.plot_data = TextPanel(self.panel,
                                   self.datasrc, 
                                   text="Additional plot information goes here")
        self.plot_panel = PlotPanel(self.panel,
                                    messenger=self.CoordMessage)

        vbox = wx.BoxSizer(wx.VERTICAL)

        vbox.Add(self.plot_panel, 2, wx.EXPAND)
        vbox.Add(self.plot_data.GetPanel(), 1, wx.EXPAND)

        self.panel.SetSizer(vbox)
    
    def CoordMessage(self, s, **kwargs):
        app = wx.GetApp()
        app.layout.status.SetStatusText(s)


class Layout(wx.Frame):

    def __init__(self, parent, title, datasrc=None):
        super(Layout, self).__init__(parent, title=title, size=(1000, 600))
        self.datasrc = datasrc
        self.InitUI()
        self.Centre()

    def InitUI(self):
        panel = wx.Panel(self)
        # Build status bar
        self.status = self.CreateStatusBar()
        self.status.SetStatusText('Ready')

        # Build menu bar
        menubar = wx.MenuBar()
        fileMenu = wx.Menu()
        # Quit option
        quitItem = fileMenu.Append(wx.ID_EXIT, 'Quit', 'Quit application')
        self.Bind(wx.EVT_MENU, self.OnQuit, quitItem)

        dataMenu = wx.Menu()
        # Load option
        loadItem = dataMenu.Append(wx.ID_OPEN, 'Load', 'Load data')
        self.Bind(wx.EVT_MENU, self.LoadData, loadItem)
        # Dummy option to test status bar
        statItem = dataMenu.Append(wx.ID_ANY, 'Compute', 'Think really hard')
        self.Bind(wx.EVT_MENU, lambda x: StartCoroutine(
            self.SlowFunc(x), self), statItem)

        # Add submenus to overall menu bar
        menubar.Append(fileMenu, '&File')
        menubar.Append(dataMenu, '&Data')
        self.SetMenuBar(menubar)

        # Build main layout
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        # Create the subclassed panels
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        plt = PlotRegion(panel, self.datasrc)
        tab = TabPanel(panel, self.datasrc, ntabs=3)
        # Create a second control
        hbox.Add(plt.GetPanel(), 2, wx.EXPAND)
        hbox.Add(tab.GetPanel(), 1, wx.EXPAND)

        panel.SetSizerAndFit(hbox)

    def OnQuit(self, e):
        '''
        Quit the application. Called by quitItem.
        '''
        self.Close()

    def LoadData(self, e):
        '''
        Load a new data trace.
        '''
        # Create dialog box
        # otherwise ask the user what new file to open
        with LoadDialog(self, title="Load a delimited file...") as dialog:

            if dialog.ShowModal() == wx.ID_CANCEL:
                return     # the user changed their mind
            # Proceed loading the file chosen by the user
            path = dialog.fileCtrl.GetPath()
            # Assemble remaining options into a dictionary
            options = {
                'delimChoice' : dialog.delimCtrl.GetSelection(),
                'header' : dialog.headCtrl.GetValue(),
                'commentChar' : dialog.commCtrl.GetValue(),
                'freqColInd' : dialog.freqIndCtrl.GetValue(),
                'skipCount' : dialog.skipCtrl.GetValue(),
                'freqUnit' : dialog.freqUnitCtrl.GetValue(),
                'specUnit' : dialog.specUnitCtrl.GetValue()
            }

            try:
                traceInd = self.datasrc.addTraceFromCSV(path, options=options)
            except IOError as e:
                wx.LogError("Cannot open file {}.".format(path))
                wx.LogError(str(e))
            print("The new trace is at index {}".format(traceInd))

    async def SlowFunc(self, e):
        '''
        Dummy function to test status bar updating asynchronously
        '''
        self.status.PushStatusText("Working...")
        await asyncio.sleep(5)
        self.status.PopStatusText()


class App(WxAsyncApp):
    def __init__(self, datasrc=None):
        self.datasrc = datasrc
        super(App, self).__init__()

    def OnInit(self):
        self.layout = Layout(None, title='Layout test', datasrc=self.datasrc)
        self.layout.Show()
        return True
