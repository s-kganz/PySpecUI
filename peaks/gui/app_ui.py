'''
This file includes implementation of derived classes for building
the application interface.
'''
# WX MODULES
import wx
from wxasync import AsyncBind, WxAsyncApp, StartCoroutine
from wxmplot import PlotPanel

# OTHER PYTHON MODULES
import time
import os
import asyncio
from asyncio import get_event_loop

# OTHER MODULES
from peaks.data.ds import DataSource
from peaks.data.spec import Spectrum
from peaks.gui.helpers import *
from peaks.gui.dialogs import *

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
        raise NotImplementedError("InitUI must be defined for all derived subpanels")

    def GetPanel(self):
        '''
        Return a pointer to the panel (i.e. the widget container) for this
        SubPanel.
        '''
        return self.panel

class CatalogTab(SubPanel):
    '''
    Implements a window for viewing files in the current working directory
    and a file selection control for changing the working directory.
    '''
    def __init__(self, parent, datasrc):
        self.cwd = os.getcwd()
        super(CatalogTab, self).__init__(parent, datasrc)

    def InitUI(self):
        vsizer = wx.BoxSizer(wx.VERTICAL)

        # Control for the current working directory
        self.dirctrl = wx.DirPickerCtrl(self.panel, path=self.cwd)
        vsizer.Add(self.dirctrl, 0)

        # View for files in the current working directory
        self.tree = DirTreeCtrl(self.panel, datasrc=self.datasrc)
        vsizer.Add(self.tree, 1, wx.EXPAND)

        self.panel.SetSizer(vsizer)

        # Bind a change in the selection to updating the field
        self.panel.Bind(wx.EVT_DIRPICKER_CHANGED, self.OnDirChanged)

    def OnDirChanged(self, event):
        newpath = self.dirctrl.GetPath()
        self.tree.setwd(newpath)

class DataTab(SubPanel):
    '''
    Implements UI elements for the trace window on the right hand side
    of the screen.
    '''
    def __init__(self, parent, datasrc):
        self.btns = []
        super(DataTab, self).__init__(parent, datasrc)
    
    def InitUI(self):
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        # Create the root nodes in the tree
        self.tree = DragAndDropTree(
            self.panel, 
            self.datasrc, 
            style=wx.TR_DEFAULT_STYLE
        )
        root = self.tree.AddRoot("Project")

        # Section headers
        self.tree_spec = self.tree.AppendItem(root, "Spectra")
        self.tree_mode = self.tree.AppendItem(root, "Models")
        self.tree_scpt = self.tree.AppendItem(root, "Scripts")
        self.tree_tchn = self.tree.AppendItem(root, "Tool Chains")

        # Show the tree by default
        self.tree.Expand(root)

        self.sizer.Add(self.tree, 1, wx.EXPAND)
        self.panel.SetSizer(self.sizer)

        # Bind events
        self.tree.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.OnDblClick)
        self.tree.Bind(wx.EVT_KEY_DOWN, self.OnKeyPress)

    def AddTrace(self, trace_idx):
        field = str(self.datasrc.traces[trace_idx])
        self.tree.AppendItem(self.tree_spec, field, data=self.datasrc.traces[trace_idx])

    def RemoveTrace(self, event):
        pass

    def OnDblClick(self, event):
        itemData = self.tree.GetItemData(event.GetItem())
        if type(itemData) == Spectrum:
            if itemData.is_plotted:
                # Remove the item from the plot
                wx.GetTopLevelParent(self.panel).RemoveTracesFromPlot([itemData.id])
                itemData.is_plotted = False
                self.tree.SetItemBold(event.GetItem(), bold=False)
            else:
                # Plot it and make it boldface
                wx.GetTopLevelParent(self.panel).AddTracesToPlot([itemData.id])
                itemData.is_plotted = True
                self.tree.SetItemBold(event.GetItem())
        else:
            # Expand/collapse this item
            if self.tree.IsExpanded(event.GetItem()):
                self.tree.Collapse(event.GetItem())
            else:
                self.tree.Expand(event.GetItem())
    
    def OnKeyPress(self, event):
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_DELETE:
            # Determine if the current selection is a spectrum
            sel_item = self.tree.GetSelection()
            sel_data = self.tree.GetItemData(sel_item)
            if type(sel_data) == Spectrum:
                # Launch a dialog to ask if the user actually wants to delete it
                with wx.MessageDialog(
                    self.panel,
                    "Do you want to remove trace {}?".format(sel_data.name),
                    style = wx.CENTRE | wx.YES_NO | wx.CANCEL
                ) as dialog:
                    if dialog.ShowModal() == wx.ID_YES:
                        # Actually delete the trace from the plot, tree, and data manager
                        self.tree.Delete(sel_item)
                        wx.GetTopLevelParent(self.panel).RemoveTracesFromPlot([sel_data.id])
                        self.datasrc.DeleteTrace(sel_data.id)
        
        event.Skip() # Pass it up the chain

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
        self.data_tab = DataTab(nb, self.datasrc)
        tabs.append(self.data_tab.GetPanel())

        self.catalog = CatalogTab(nb, self.datasrc)
        tabs.append(self.catalog.GetPanel())
  
        # Names of each tab
        names = ["Data", "Directory"]
        # Add all tabs to the notebook object
        assert(len(names) == len(tabs))
        for i in range(len(tabs)):
            nb.AddPage(tabs[i], names[i])

        # Place notebook in a sizer so it expands to the size of the panel
        sizer = wx.BoxSizer()
        sizer.Add(nb, 1, wx.EXPAND)

        self.panel.SetSizer(sizer)

class TextPanel(SubPanel):
    '''
    Static panel showing a centered StaticText control
    '''
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
        self.is_blank = True
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
        self.is_blank = True
        self.plot_panel.reset_config() # Remove old names of traces
        if len(self.plotted_traces) > 0:
            for id in self.plotted_traces:
                # Get the trace from the data manager
                spec = self.datasrc.GetTraceByID(id)
                assert(spec) # Make sure spectrum is not null
                self.PlotTrace(spec)
        else:
            self.plot_panel.clear() # This call forces the plot to update visually
            self.plot_panel.unzoom_all()

    def PlotTrace(self, t, **kwargs):
        '''
        Plot a trace object. Used internally to standardize plotting style.
        '''
        if self.is_blank:
            self.plot_panel.plot(t.getx(), t.gety(), label=t.name, show_legend=True, **kwargs)
            self.is_blank = False
        else:
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

    def LoadData(self, e, **kwargs):
        '''
        Load a new data trace.
        '''
        # Create dialog box
        with LoadDialog(self, **kwargs) as dialog:

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

def start_app():
    ds = DataSource()
    app = App(datasrc=ds)
    loop = get_event_loop()
    loop.run_until_complete(app.MainLoop())