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
from peaks.data.models import Model
from peaks.data.data_helpers import Trace
from peaks.gui.ui_helpers import *
from peaks.gui.dialogs import *
from peaks.gui.popups import *


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
        raise NotImplementedError(
            "InitUI must be defined for all derived subpanels")

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
        super(CatalogTab, self).__init__(parent, datasrc)

    def InitUI(self):
        vsizer = wx.BoxSizer(wx.VERTICAL)

        # View for files in the current working directory
        self.tree = wx.GenericDirCtrl(self.panel, dir=os.getcwd())
        self.tree.Bind(wx.EVT_DIRCTRL_FILEACTIVATED, self.OnDblClick)
        vsizer.Add(self.tree, 1, wx.EXPAND)

        self.panel.SetSizer(vsizer)

    def OnDblClick(self, event):
        act_item = event.GetItem()
        if not self.tree.GetTreeCtrl().GetChildrenCount(act_item) > 0:
            # Get the path associated with this tree item and load it
            abspath = self.tree.GetPath(act_item)
            wx.GetTopLevelParent(self.panel).LoadData(None, path=abspath)


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
        self.tree.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK, self.OnRgtClick)

    # Tree modifiers
    def AddTrace(self, trace_id, type='spec'):
        '''
        Add a new trace to the tree
        '''
        trace = self.datasrc.GetTraceByID(trace_id)
        hook = self.tree_spec if type == 'spec' else self.tree_mode

        try:
            assert(trace is not None)
        except AssertionError:
            raise AssertionError("AddTrace received a null trace object!")

        field = str(trace)
        newid = self.tree.AppendItem(hook, field, data=trace)
        self.tree.EnsureVisible(newid)

    def RemoveTrace(self, trace_item):
        '''
        Remove a trace from the tree, including from the plot window
        if the spectrum is currently plotted.
        '''
        trace_data = self.tree.GetItemData(trace_item)
        with wx.MessageDialog(
            self.panel,
            "Do you want to remove trace {}?".format(trace_data.label()),
            style=wx.CENTRE | wx.YES_NO | wx.CANCEL
        ) as dialog:
            if dialog.ShowModal() == wx.ID_YES:
                # Actually delete the trace from the plot, tree, and data manager
                self.tree.Delete(trace_item)
                wx.GetTopLevelParent(self.panel).RemoveTraceFromPlot(trace_data.id)
                self.datasrc.DeleteTrace(trace_data.id)

    def TogglePlotted(self, trace_item):
        '''
        Toggles whether the trace object is shown in the plot window.
        '''
        trace = self.tree.GetItemData(trace_item)
        if trace.is_plotted:
            # Remove the item from the plot
            wx.GetTopLevelParent(self.panel).RemoveTraceFromPlot(trace.id)
            trace.is_plotted = False
            self.tree.SetItemBold(trace_item, bold=False)
        else:
            # Plot it and make it boldface
            wx.GetTopLevelParent(self.panel).AddTraceToPlot(trace.id)
            trace.is_plotted = True
            self.tree.SetItemBold(trace_item, bold=True)

    # Event handlers
    def OnDblClick(self, event):
        '''
        Handles double-click events on tree entries. Depending on item type,
        has the following behavior:

        Spectrum: toggles whether the spectrum is plotted
        Nodes: toggles whether the node is expanded/collapsed
        '''
        item = event.GetItem()
        if issubclass(type(self.tree.GetItemData(item)), Trace):
            self.TogglePlotted(item)
        else:
            # Expand/collapse this item
            if self.tree.IsExpanded(item):
                self.tree.Collapse(item)
            else:
                self.tree.Expand(item)

    def OnKeyPress(self, event):
        '''
        Handles key-press events. Defined for the following keys:

        DELETE: If the highlighted tree item is a Spectrum, launch
        a removal dialog window.
        '''
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_DELETE:
            # Determine if the current selection is a spectrum
            sel_item = self.tree.GetSelection()
            sel_data = self.tree.GetItemData(sel_item)
            if type(sel_data) == Spectrum:
                self.RemoveTrace(sel_item)

        event.Skip()  # Pass it up the chain

    def OnRgtClick(self, event):
        '''
        Handles right-click events by launching a context menu.
        Defined for the following item types:

        Spectrum: Shows a Remove | Add to plot popup menu. (See Menu_TreeCtrlSpectrum)
        '''
        # Figure out the type of the item involved
        clk_item = event.GetItem()
        popup = None
        if issubclass(type(self.tree.GetItemData(clk_item)), Trace):
            popup = Menu_TreeCtrlTrace(self, clk_item)

        if popup:
            self.tree.PopupMenu(popup, event.GetPoint())


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

        self.panel.SetSizerAndFit(sizer)


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

        self.panel.SetSizerAndFit(vbox)

    def CoordMessage(self, s, **kwargs):
        app = wx.GetApp()
        app.layout.status.SetStatusText(s)

    def AddTracesToPlot(self, traces):
        '''
        Reset the current plot and show all passed traces
        '''
        to_plot = []
        self.plotted_traces.clear()
        for t in self.datasrc.traces:
            if t.id in traces:
                to_plot.append(t)
                self.plotted_traces.append(t.id)

        self.PlotMany(to_plot)

    def AddTraceToPlot(self, trace):
        '''
        Add a single trace to the plot
        '''
        self.PlotTrace(self.datasrc.GetTraceByID(trace))
        self.plotted_traces.append(trace)

    def RemoveTraceFromPlot(self, trace):
        '''
        Remove a single trace from the plot
        '''
        i = 0
        while i < len(self.plotted_traces):
            if self.plotted_traces[i] == trace:
                self.plotted_traces.pop(i)
                break
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
        self.plot_panel.reset_config()  # Remove old names of traces
        if len(self.plotted_traces) > 0:
            to_plot = list()
            for id in self.plotted_traces:
                # Get the trace from the data manager
                spec = self.datasrc.GetTraceByID(id)
                assert(spec)  # Make sure trace is not null
                to_plot.append(spec)
            self.PlotMany(to_plot)
        else:
            self.plot_panel.clear()  # This call forces the plot to update visually
            self.plot_panel.unzoom_all()

    def PlotTrace(self, t, **kwargs):
        '''
        Plot a trace object. Used internally to standardize plotting style.
        '''
        if self.is_blank:
            self.plot_panel.plot(t.getx(), t.gety(),
                                 label=t.label(), show_legend=True, **kwargs)
            self.is_blank = False
        else:
            self.plot_panel.oplot(t.getx(), t.gety(),
                                  label=t.label(), show_legend=True, **kwargs)

    def PlotMany(self, traces, **kwargs):
        '''
        Plot a list of trace objects
        '''
        if len(traces) > 0:
            # Get x and y arrays for each trace and associate labels with each
            plot_dict = [
                {
                    'xdata': t.getx(),
                    'ydata': t.gety(),
                    'label': t.label()}
                for t in traces
            ]
            self.plot_panel.plot_many(plot_dict, show_legend=True)
            self.is_blank = False


class Layout(wx.Frame):

    def __init__(self, parent, title, datasrc=None):
        super(Layout, self).__init__(parent, title=title, size=(1000, 600))
        self.datasrc = datasrc
        self.InitUI()
        self.Centre()

    def InitUI(self):
        # Build status bar
        self.status = self.CreateStatusBar()
        self.status.SetStatusText('Ready')

        # Build menu bar
        menubar = wx.MenuBar()

        # File submenu
        fileMenu = wx.Menu()
        # Quit option
        quitItem = fileMenu.Append(wx.ID_EXIT, 'Quit', 'Quit application')
        self.Bind(wx.EVT_MENU, self.OnQuit, quitItem)

        # Data submenu
        dataMenu = wx.Menu()
        # Load option
        loadItem = dataMenu.Append(wx.ID_OPEN, 'Load', 'Load data')
        self.Bind(wx.EVT_MENU, self.LoadData, loadItem)
        # Dummy option to test status bar
        statItem = dataMenu.Append(wx.ID_ANY, 'Compute', 'Think really hard')
        self.Bind(wx.EVT_MENU, lambda x: StartCoroutine(
            self.SlowFunc(x), self), statItem)

        # Fitting submeni
        fitMenu = wx.Menu()
        gaussItem = fitMenu.Append(
            wx.ID_ANY, 'Gaussian...', 'Fit Gaussian peaks to a spectrum')
        self.Bind(wx.EVT_MENU, self.OnFitGauss, gaussItem)

        # Add submenus to overall menu bar
        menubar.Append(fileMenu, '&File')
        menubar.Append(dataMenu, '&Data')
        menubar.Append(fitMenu, 'F&it')
        self.SetMenuBar(menubar)

        # Build the main layout, splitting between the left and right
        # Live update prevents flashing a black line on resize
        splitter = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE)

        self.plt_pane = PlotRegion(splitter, self.datasrc)
        self.tab_pane = TabPanel(splitter, self.datasrc, ntabs=3)

        splitter.SplitVertically(
            self.plt_pane.GetPanel(), self.tab_pane.GetPanel())
        splitter.SetMinimumPaneSize(300)

        # Put the splitter in a sizer
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(splitter, 1, wx.EXPAND)
        self.SetSizerAndFit(sizer)
        self.Centre()

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
        with DialogLoad(self, **kwargs) as dialog:

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
                traceInd = self.datasrc.AddTraceFromCSV(path, options=options)
            except IOError as e:
                wx.LogError("Cannot open file {}.".format(path))
                wx.LogError(str(e))
                return

            if traceInd >= 0:
                # Add the new trace to the tab panel
                self.tab_pane.data_tab.AddTrace(traceInd, type='spec')

    def AddTraceToPlot(self, trace):
        '''
        Pull the given trace from the data manager and add it to the plot
        '''
        self.plt_pane.AddTraceToPlot(trace)

    def RemoveTraceFromPlot(self, trace):
        '''
        Remove the given traces from the plot window.
        '''
        self.plt_pane.RemoveTraceFromPlot(trace)

    def UpdatePlotTraces(self, traces):
        '''
        Replot the given traces
        '''
        self.plt_pane.UpdatePlotTraces(traces)

    def OnFitGauss(self, event):
        '''
        Create a dialog for fitting Gaussian peaks to
        spectra currently loaded.
        '''
        # Get all the spectra and their ids from the data manager
        names = dict()
        names = {
            t.name: t.id for t in self.datasrc.traces if type(t) == Spectrum}

        # Don't try to fit if no spectra are loaded
        if not len(names) > 0:
            with wx.MessageDialog(self, "No spectra available to fit.") as dialog:
                dialog.ShowModal()
                return

        with DialogGaussModel(self, names) as dialog:
            if dialog.ShowModal() == wx.ID_CANCEL:
                # they don't wanna fit after all :(
                return
            else:
                # Get the spectrum to fit on
                spec_sel = dialog.ctrl_spec_name.GetSelection()
                spec_id = names[dialog.ctrl_spec_name.GetString(spec_sel)]

                # Additional arguments for the fitting procedure
                kwargs = {
                    'peak_range': (
                        dialog.ctrl_min_peaks.GetValue(),
                        dialog.ctrl_max_peaks.GetValue()
                    ),
                    'polyorder': dialog.ctrl_poly_order.GetValue()
                }
                # Make the model
                try:
                    ret = self.datasrc.CreateGaussModel(spec_id, **kwargs)
                except Exception as e:
                    wx.LogError(str(e))
                    return

                # Add the new model to the data tab
                self.tab_pane.data_tab.AddTrace(ret, type='model')
                return ret

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
        self.layout = Layout(None, title='PyPeaks', datasrc=self.datasrc)
        self.layout.Show()
        return True


def start_app():
    ds = DataSource()
    app = App(datasrc=ds)
    loop = get_event_loop()
    loop.run_until_complete(app.MainLoop())
