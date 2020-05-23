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

class SubPanel():
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

class DirTreeCtrl(wx.TreeCtrl):
    '''
    A window showing the current working directory. Implementation comes from:
    https://python-forum.io/Thread-Use-custom-root-in-wx-GenericDirCtrl
    '''
    def __init__(self, parent, datasrc=None):
        super(DirTreeCtrl, self).__init__(parent)
        self.__collapsing = True
        self.datasrc = datasrc
 
        il = wx.ImageList(16,16)
        self.folderidx = il.Add(wx.ArtProvider.GetBitmap(wx.ART_FOLDER, wx.ART_OTHER, (16,16)))
        self.fileidx = il.Add(wx.ArtProvider.GetBitmap(wx.ART_NORMAL_FILE, wx.ART_OTHER, (16,16)))
        self.AssignImageList(il)
 
        root = os.getcwd()
        self.setwd(root)

    def setwd(self, newdir):
        ids = {newdir : self.AddRoot(newdir, self.folderidx)}
        self.SetItemHasChildren(ids[newdir])
 
        for (dirpath, dirnames, filenames) in os.walk(newdir):
            for dirname in sorted(dirnames):
                fullpath = os.path.join(dirpath, dirname)
                ids[fullpath] = self.AppendItem(ids[dirpath], dirname, self.folderidx)
                 
            for filename in sorted(filenames):
                self.AppendItem(ids[dirpath], filename, self.fileidx)

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
        self.delimCtrl = wx.Choice(
            parse_pane, choices=["Tab", "Comma", "Space"])
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

class DataTab(SubPanel):
    '''
    Implements UI elements for the trace window on the right hand side
    of the screen.
    '''
    def __init__(self, parent, datasrc):
        self.btns = []
        super(DataTab, self).__init__(parent, datasrc)
    
    def InitUI(self):
        # The first tab lists all data currently loaded
        trace_pane = self.panel
        trace_sizer = wx.BoxSizer(wx.VERTICAL)

        # Mixin listctrl for selecting traces
        self.trace_list = ResizeListCtrl(
            trace_pane, size=(-1, 100), style=wx.LC_REPORT
        )
        self.trace_list.InsertColumn(0, 'Name', width=-1)
        self.trace_list.InsertColumn(1, 'Freq Unit', width=-1)
        self.trace_list.InsertColumn(2, 'Spec Unit', width=-1)
        trace_sizer.Add(self.trace_list, wx.EXPAND)

        # Additional controls at the bottom of the data tab
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Button for removing traces
        self.rm_btn = wx.Button(trace_pane, label="Remove")
        self.rm_btn.Disable()  # start in disabled state
        trace_pane.Bind(wx.EVT_BUTTON, self.RemoveTrace, self.rm_btn)
        self.btns.append(self.rm_btn)

        # Button for adding traces to the plot
        self.plot_btn = wx.Button(trace_pane, label="Add to plot")
        self.plot_btn.Disable()
        trace_pane.Bind(wx.EVT_BUTTON, self.OnPlot, self.plot_btn)
        self.btns.append(self.plot_btn)

        btn_sizer.Add(self.rm_btn, wx.CENTER)
        btn_sizer.Add(self.plot_btn, wx.CENTER)
        trace_sizer.Add(btn_sizer, 0, wx.EXPAND)
        trace_pane.SetSizer(trace_sizer)

        # Bind selection/deselection of list elements to updating buttons
        trace_pane.Bind(wx.EVT_LIST_ITEM_SELECTED,
                        self.UpdateButtons, self.trace_list)
        trace_pane.Bind(wx.EVT_LIST_ITEM_DESELECTED,
                        self.UpdateButtons, self.trace_list)

    def AddTrace(self, trace_idx):
        # Get fields for the new trace
        spec = self.datasrc.traces[trace_idx]
        fields = (spec.name, spec.frequnit, spec.specunit)
        # Add a new row to the list control
        self.trace_list.Append(fields)

    def UpdateButtons(self, event):
        '''
        Enable or Disable the removal button at the bottom of the data tab depending
        on if any of traces are selected.
        '''
        if any(self.trace_list.IsSelected(i) for i in range(0, self.trace_list.GetItemCount())):
            # Activate all buttons
            for btn in self.btns:
                btn.Enable()
        else:
            # Disable all buttons
            for btn in self.btns:
                btn.Disable()
        event.Skip()

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
                # Also remove the trace from the plot
                wx.GetTopLevelParent(self.panel).RemoveTracesFromPlot([self.datasrc.traces[i].id])
                # Delete the trace from the data manager as well
                # The assertion will fail if the data manager trace array
                # is out of sync with the listctrl's array
                try:
                    assert(self.datasrc.DeleteTrace(i))
                    continue  # don't increment index if a deletion occurs
                except:
                    raise RuntimeError(
                        "Failed to delete trace at index {}".format(i))
            i += 1
    
    def OnPlot(self, event):
        '''
        Add selected traces to the plot window, showing warnings about axis
        limits as necessary.
        '''
        # Determine which traces IDs are selected and pass these to the plot panel
        selected = [self.datasrc.traces[i].id \
                    for i in range(0, self.trace_list.GetItemCount()) \
                    if self.trace_list.IsSelected(i)]

        wx.GetTopLevelParent(self.panel).AddTracesToPlot(selected)

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
        self.data_tab = DirTreeCtrl(nb, self.datasrc)
        tabs.append(self.data_tab)
  
        # Names of each tab
        names = ["Catalog"]
        # Create notebook object
        assert(len(names) == len(tabs))
        for i in range(len(tabs)):
            nb.AddPage(tabs[i], names[i])

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
        self.plotted_traces = []
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
    
    def AddTracesToPlot(self, traces):
        # Add data to the plot if it is not already present
        for t in self.datasrc.traces:
            if (t.id in traces) and (t.id not in self.plotted_traces):
                self.PlotTrace(t)
                self.plotted_traces.append(t.id)
    
    def RemoveTracesFromPlot(self, traces):
        # Remove traces to be discarded
        i = 0
        while i < len(self.plotted_traces):
            if self.plotted_traces[i] in traces:
                self.plotted_traces.pop(i)
                continue
            i += 1
        # Clear and re-draw the plot
        self.Replot()

    def UpdateTraces(self, traces):
        # stub
        # Replot the passed traces if they are present
        print("Updating traces {}".format(traces))
    
    def Replot(self):
        '''
        Replot all loaded traces.
        '''
        self.plot_panel.clear()
        self.plot_panel.reset_config() # Remove old names of traces
        if len(self.plotted_traces) > 0:
            for id in self.plotted_traces:
                # Get the trace from the data manager
                spec = self.datasrc.GetTraceByID(id)
                assert(spec) # Make sure spectrum is not null
                self.PlotTrace(spec)
        else:
            self.plot_panel.unzoom_all() # This call forces the plot to update visually

    def PlotTrace(self, t, **kwargs):
        '''
        Plot a trace object. Used internally to standardize plotting style.
        '''
        self.plot_panel.oplot(t.getx(), t.gety(), label=t.name, show_legend=True, **kwargs)

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
            delimStr = dialog.delimCtrl.GetString(
                dialog.delimCtrl.GetSelection())
            commChar = dialog.commCtrl.GetValue()
            if len(commChar) == 0:
                commChar = None
            options = {
                'delimChoice': delimStr,
                'header': dialog.headCtrl.GetValue(),
                'commentChar': commChar,
                'freqColInd': dialog.freqIndCtrl.GetValue(),
                'skipCount': dialog.skipCtrl.GetValue(),
                'freqUnit': dialog.freqUnitCtrl.GetValue(),
                'specUnit': dialog.specUnitCtrl.GetValue()
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
                self.tab_pane.data_tab.AddTrace(traceInd)

    def AddTracesToPlot(self, traces):
        '''
        Pull the given traces from the data manager and add them to the
        plot.
        '''
        self.plt_pane.AddTracesToPlot(traces)

    def RemoveTracesFromPlot(self, traces):
        '''
        Remove the given traces from the plot window.
        '''
        self.plt_pane.RemoveTracesFromPlot(traces)
    
    def UpdatePlotTraces(self, traces):
        '''
        Replot the given traces
        '''
        self.plt_pane.UpdatePlotTraces(traces)

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
