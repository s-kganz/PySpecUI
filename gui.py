'''
This file includes implementation of derived classes for building
the application interface.
'''

import wx
from wx.lib.intctrl import IntCtrl
from wx.lib import sized_controls
from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin
from wxasync import AsyncBind, WxAsyncApp, StartCoroutine
from wxmplot import PlotPanel

import time
import os
import asyncio

class ResizeListCtrl(wx.ListCtrl, ListCtrlAutoWidthMixin):
    '''
    Adding the auto width mixin makes the ListCtrl resize itself properly. Otherwise
    this is exactly the same as a typical ListCtrl.
    '''
    def __init__(self, parent, ID=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=wx.LC_REPORT):
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
        ListCtrlAutoWidthMixin.__init__(self)
        self.setResizeColumn(0)

class LoadDialog(sized_controls.SizedDialog):
    '''
    Dialog box for loading a data file.
    '''
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
        self.delimCtrl.SetSelection(0)

        # Header choice
        wx.StaticText(parse_pane, label="Parse headers: ")
        self.headCtrl = wx.CheckBox(parse_pane)

        # Comment character
        wx.StaticText(parse_pane, label="Comment character: ")
        self.commCtrl = wx.TextCtrl(parse_pane, value='#')
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
        self.data_tab_idx = 0
        super(TabPanel, self).__init__(parent, datasrc)

    def InitUI(self):
        '''
        Initialize self.ntabs panels
        '''
        # Create notebook object
        nb = wx.Notebook(self.panel)
        # Create tab objects
        tabs = []

        # The first tab lists all data currently loaded
        trace_pane = wx.Panel(nb)
        trace_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Mixin listctrl for selecting traces
        self.trace_list = ResizeListCtrl(trace_pane, size=(-1, 100), style=wx.LC_REPORT)
        self.trace_list.InsertColumn(0, 'Name', width=-1)
        self.trace_list.InsertColumn(1, 'Freq Unit', width=-1)
        self.trace_list.InsertColumn(2, 'Spec Unit', width=-1)
        trace_sizer.Add(self.trace_list, wx.EXPAND)
        
        # Button for removing traces
        self.rm_btn = wx.Button(trace_pane, label="Remove")
        self.rm_btn.Disable() # start in disabled state
        self.parent.Bind(wx.EVT_BUTTON, self.RemoveTrace, self.rm_btn)
        trace_sizer.Add(self.rm_btn)
        main_sizer.Add(trace_sizer, 1, wx.EXPAND)
        trace_pane.SetSizer(main_sizer)
        tabs.append(trace_pane)

        # Bind selection/deselection of list elements to updating the button
        trace_pane.Bind(wx.EVT_LIST_ITEM_SELECTED, self.UpdateRmButton, self.trace_list)
        trace_pane.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.UpdateRmButton, self.trace_list)

        # Names of each tab
        names = ["Data"]
        # Create notebook object
        assert(len(names) == len(tabs))
        for i in range(len(tabs)):
            nb.AddPage(tabs[i], names[i])

        # Place notebook in a sizer so it expands to the size of the panel
        sizer = wx.BoxSizer()
        sizer.Add(nb, 1, wx.EXPAND)

        self.panel.SetSizer(sizer)
    
    def AddTrace(self, trace_idx):
        # Get fields for the new trace
        spec = self.datasrc.traces[trace_idx]
        fields = (spec.name, spec.frequnit, spec.specunit)
        # Add a new row to the list control
        self.trace_list.Append(fields)

    def UpdateRmButton(self, event):
        '''
        Enable or Disable the removal button at the bottom of the data tab depending
        on if any of traces are selected.
        '''
        if any(self.trace_list.IsSelected(i) for i in range(0, self.trace_list.GetItemCount())):
            self.rm_btn.Enable()
        else:
            self.rm_btn.Disable()

    def ActivateRmButton(self, event):
        '''
        Responds to EVT_LIST_ITEM_SELECTED events.
        '''
        self.rm_btn.Enable()

    def DeactivateRmButton(self, event):
        '''
        Responds to EVT_LIST_ITEM_DESELECTED events.
        '''
        self.rm_btn.Disable()

    def RemoveTrace(self, event):
        '''
        Event handler to remove traces.
        NOTE: The array of traces in the data manager should be in the exact
              same order the array of traces shown in the list control.
        '''
        # Iterate over all items in the list. If one is selected, remove it.
        i = 0
        while i < self.trace_list.GetItemCount():
            if self.trace_list.IsSelected(i):
                self.trace_list.DeleteItem(i)
                # Delete the trace from the data manager as well
                # The assertion will fail if the data manager trace array
                # is out of sync with the listctrl's array
                try:
                    assert(self.datasrc.DeleteTrace(i))
                    continue # don't increment index if a deletion occurs
                except:
                    raise RuntimeError("Failed to delete trace at index {}".format(i))
            i += 1

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
        self.plt_pane = PlotRegion(panel, self.datasrc)
        self.tab_pane = TabPanel(panel, self.datasrc, ntabs=3)
        # Create a second control
        hbox.Add(self.plt_pane.GetPanel(), 2, wx.EXPAND)
        hbox.Add(self.tab_pane.GetPanel(), 1, wx.EXPAND)

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
        with LoadDialog(self, title="Load a delimited file...") as dialog:

            if dialog.ShowModal() == wx.ID_CANCEL:
                return     # the user changed their mind
            # Proceed loading the file chosen by the user
            path = dialog.fileCtrl.GetPath()
            # Assemble remaining options into a dictionary
            delimStr = dialog.delimCtrl.GetString(dialog.delimCtrl.GetSelection())
            commChar = dialog.commCtrl.GetValue()
            if len(commChar) == 0: commChar = None
            options = {
                'delimChoice' : delimStr,
                'header' : dialog.headCtrl.GetValue(),
                'commentChar' : commChar,
                'freqColInd' : dialog.freqIndCtrl.GetValue(),
                'skipCount' : dialog.skipCtrl.GetValue(),
                'freqUnit' : dialog.freqUnitCtrl.GetValue(),
                'specUnit' : dialog.specUnitCtrl.GetValue()
            }
            traceInd = -1
            try:
                traceInd = self.datasrc.addTraceFromCSV(path, options=options)
            except IOError as e:
                wx.LogError("Cannot open file {}.".format(path))
                wx.LogError(str(e))
                return
            
            if traceInd >= 0:
                # Add the new trace to the tab panel
                self.tab_pane.AddTrace(traceInd)
            

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
