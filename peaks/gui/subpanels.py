'''
Implementation of classes derived from wx controls and specific subpanels
of the application.
'''

# GENERAL MODULES
from pubsub import pub
import asyncio
import os
import math

# WXPYTHON MODULES
import wx
from wxmplot import PlotPanel

# NAMESPACE MODULES
from peaks.data.data_helpers import Trace
from peaks.data.ds import DataSource
from peaks.data.spec import Spectrum
from .dialogs import *
from .popups import *
from .ui_helpers import *


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
            "InitUI must be defined for all derived subpanels"
        )

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
        '''
        Create widgets.
        '''
        vsizer = wx.BoxSizer(wx.VERTICAL)

        # View for files in the current working directory
        self.tree = wx.GenericDirCtrl(self.panel, dir=os.getcwd())
        self.tree.Bind(wx.EVT_DIRCTRL_FILEACTIVATED, self.OnDblClick)
        vsizer.Add(self.tree, 1, wx.EXPAND)

        self.panel.SetSizer(vsizer)

    def OnDblClick(self, event):
        '''
        Event handler for double clicking on an item in the file
        window.
        '''
        act_item = event.GetItem()
        if not self.tree.GetTreeCtrl().GetChildrenCount(act_item) > 0:
            # The item is a leaf, try and load it.
            abspath = self.tree.GetPath(act_item)
            dialog_data = {
                'path': abspath
            }
            pub.sendMessage('Dialog.Run', D=DialogLoad,
                            data=dialog_data)


class DataTab(SubPanel):
    '''
    Implements UI elements for the trace window on the right hand side
    of the screen.
    '''

    def __init__(self, parent, datasrc):
        self.btns = []
        super(DataTab, self).__init__(parent, datasrc)

        pub.subscribe(self.AddTrace, 'UI.Tree.AddTrace')

    def InitUI(self):
        '''
        Create widgets.
        '''
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        # Create the root nodes in the tree
        self.tree = wx.TreeCtrl(
            self.panel,
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
    def AddTrace(self, trace, type='spec'):
        '''
        Add a new trace to the tree
        '''
        # Determine which heading the new item should go under
        hook = self.tree_spec if type == 'spec' else self.tree_mode

        try:
            assert(trace is not None)
        except AssertionError:
            raise ValueError("DataTab received a null trace object.")

            return

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
                pub.sendMessage('Data.DeleteTrace', target_id=trace_data.id)

    def TogglePlotted(self, trace_item):
        '''
        Toggles whether the trace object is shown in the plot window.
        '''
        trace = self.tree.GetItemData(trace_item)
        if trace.is_plotted:
            # Remove the item from the plot
            pub.sendMessage('Plotting.RemoveTrace', t_id=trace.id)
            self.tree.SetItemBold(trace_item, bold=False)
        else:
            trace.is_plotted = True
            # Plot it and make it boldface
            pub.sendMessage('Plotting.AddTrace', t_id=trace.id)
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
        # Determine if the doubleclicked object is plottable
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
            if issubclass(type(sel_data), Trace):
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
            popup = Menu_TreeCtrlTrace(
                self, clk_item, self.tree.GetItemData(clk_item))

        if popup:
            self.tree.PopupMenu(popup, event.GetPoint())


class TabPanel(SubPanel):
    '''
    Class implementing a notebook-style collection of panels.
    '''

    def __init__(self, parent, datasrc):
        self.data_tab_idx = 0
        self.model_tuner = None
        self.model_tuner_idx = None
        super(TabPanel, self).__init__(parent, datasrc)

        pub.subscribe(self.CreateModelTuner, 'Data.Model.Tune')
        pub.subscribe(self.DestroyModelTuner, 'Data.Model.EndTune')

    def InitUI(self):
        '''
        Initialize self.ntabs panels
        '''
        # Create notebook object
        self.nb = wx.Notebook(self.panel)
        # Create tab objects
        tabs = []
        self.data_tab = DataTab(self.nb, self.datasrc)
        tabs.append(self.data_tab.GetPanel())

        self.catalog = CatalogTab(self.nb, self.datasrc)
        tabs.append(self.catalog.GetPanel())

        # Names of each tab
        names = ["Data", "Directory"]
        # Add all tabs to the notebook object
        assert(len(names) == len(tabs))
        for i in range(len(tabs)):
            self.nb.AddPage(tabs[i], names[i])

        # Place notebook in a sizer so it expands to the size of the panel
        sizer = wx.BoxSizer()
        sizer.Add(self.nb, 1, wx.EXPAND)

        self.panel.SetSizerAndFit(sizer)

    def CreateModelTuner(self, model=None):
        '''
        Launch a model tuning dialog as a new page in the notebook.
        '''
        # verify integrity of passed object
        if not model:
            raise ValueError("Model tuner received a null model object.")
        if not issubclass(type(model), Model):
            raise ValueError(
                "Model tuner cannot tune an object that is not a model subclass.")

        # Verify that another tuner is not active
        if self.model_tuner is not None:
            with wx.MessageDialog(
                None,
                "Another tune window is open. Close the other window before "
                "starting another tuner",
                caption='Cannot Start Tuner',
                style=wx.OK | wx.ICON_WARNING
            ) as msgbox:
                msgbox.ShowModal()
                return

        # Create the subpanel to append to the data tab
        self.model_tuner = ModelTunePanel(self.nb, model)
        self.nb.AddPage(self.model_tuner.GetPanel(), 'Model Tuner', select=True)
    
    def DestroyModelTuner(self):
        '''
        End model tuning by destroying the notebook page.
        '''
        if self.model_tuner is None:
            raise RuntimeError("DestroyModelTuner was called, but the tuner does not exist.")
        tuner_idx = self.nb.FindPage(self.model_tuner.GetPanel())
        if tuner_idx == wx.NOT_FOUND:
            raise RuntimeError("Did not find page corresponding to model tuner")
        self.nb.DeletePage(tuner_idx)
        self.model_tuner = None
        

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
    '''
    Class implementing the plot window. Utilizes a wxmplot
    PlotPanel for plotting and includes member functions for efficient
    plotting/replotting of spectra.
    '''

    def __init__(self, parent, datasrc):
        # List of trace ID's that have already been plotted
        app = wx.GetApp()
        self.plotted_traces = []
        self.is_blank = True
        super(PlotRegion, self).__init__(parent, datasrc)
        pub.subscribe(self.AddTraceToPlot, 'Plotting.AddTrace')
        pub.subscribe(self.RemoveTraceFromPlot, 'Plotting.RemoveTrace')
        pub.subscribe(self.Replot, 'Plotting.Replot')

    def _SuppressStatus(self, *args, **kwargs):
        '''
        Suppress PlotPanel messenger calls.
        '''
        return

    def InitUI(self):
        '''
        Create widgets.
        '''
        self.plot_data = TextPanel(self.panel,
                                   self.datasrc,
                                   text="Additional plot information goes here")
        self.plot_panel = PlotPanel(self.panel, messenger=self._SuppressStatus)

        vbox = wx.BoxSizer(wx.VERTICAL)

        vbox.Add(self.plot_panel, 1, wx.EXPAND)
        vbox.Add(self.plot_data.GetPanel(), 0, wx.EXPAND)

        self.panel.SetSizerAndFit(vbox)

    def AddTracesToPlot(self, traces):
        '''
        Reset the current plot and show all passed traces
        '''
        to_plot = []
        self.plotted_traces.clear()
        for t in self.datasrc.traces:
            if t.id in traces:
                t.is_plotted = True
                to_plot.append(t)
                self.plotted_traces.append(t.id)

        self.PlotMany(to_plot)

    def AddTraceToPlot(self, t_id):
        '''
        Add a single trace to the plot
        '''
        def run(t_id):
            pub.sendMessage('UI.SetStatus', text='Adding trace...')
            self.PlotTrace(self.datasrc.GetTraceByID(t_id))
            self.plotted_traces.append(t_id)
            pub.sendMessage('UI.SetStatus', text='Done.')

        asyncio.get_running_loop().run_in_executor(
            wx.GetApp().PlotThread(), lambda: run(t_id)
        )

    def RemoveTraceFromPlot(self, t_id):
        '''
        Remove a single trace from the plot. Remove the id from the internal
        list of plotted traces and set internal trace.is_plotted property
        to False.
        '''
        # The blocking segment of this routine is the replotting,
        # so management of the internal IDs can happen before the thread
        # starts to prevent out of turn trace IO operations.
        t_obj = self.datasrc.GetTraceByID(t_id)
        if t_obj:
            t_obj.is_plotted = False

        try:
            self.plotted_traces.remove(t_id)
        except ValueError:
            raise RuntimeError(
                "Plot window does not have trace with id {}".format(t_id))

        asyncio.get_running_loop().run_in_executor(
            wx.GetApp().PlotThread(), lambda: self.Replot()
        )

    def UpdateTraces(self, traces):
        '''
        Updating a single trace without re-rendering the entire
        plot window is not currently supported.
        '''
        raise NotImplementedError(
            'Updating traces not supported. Use Replot() instead.')

    def Replot(self):
        '''
        Replot all loaded traces.
        '''
        def do_plot():
            pub.sendMessage('UI.SetStatus', text='Drawing...')
            self.is_blank = True
            self.plot_panel.reset_config()  # Remove old names of traces
            if len(self.plotted_traces) > 0:
                to_plot = list()
                for id in self.plotted_traces:
                    # Get the trace from the data manager
                    spec = self.datasrc.GetTraceByID(id)
                    if not spec:
                        continue  # Make sure the spectrum isn't null
                    to_plot.append(spec)
                    spec.is_plotted = True
                self.PlotMany(to_plot)
            else:
                self.plot_panel.clear()  # This call forces the plot to update visually
                self.plot_panel.unzoom_all()
            pub.sendMessage('UI.SetStatus', text='Done.')

        asyncio.get_running_loop().run_in_executor(
            wx.GetApp().PlotThread(), lambda: do_plot()
        )

    def PlotTrace(self, t_obj, **kwargs):
        '''
        Plot a trace object. Used internally to standardize plotting style.
        '''
        if self.is_blank:
            self.plot_panel.plot(t_obj.getx(), t_obj.gety(),
                                 label=t_obj.label(), show_legend=True, **kwargs)
            t_obj.is_plotted = True
            self.is_blank = False
        else:
            self.plot_panel.oplot(t_obj.getx(), t_obj.gety(),
                                  label=t_obj.label(), show_legend=True, **kwargs)

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
                    'label': t.label()
                }
                for t in traces
            ]
            self.plot_panel.plot_many(plot_dict, show_legend=True)
            self.is_blank = False


class ModelTunePanel(SubPanel):
    '''
    Class that enables real-time modification of model parameters in
    the tab panel.
    '''

    def __init__(self, parent, model):
        '''
        Attach this object to the notebook and build widgets
        dynamically from the passed model object.
        '''
        self.model = model
        self.param_ctrls = [] # get handles into all the controls
        self.initial_params = [] # model parameter values before tuning
        super(ModelTunePanel, self).__init__(
            parent, None)  # datasrc unnecessary

    def InitUI(self):
        '''
        Dynamically build widgets for tuning the model from the object itself.
        '''
        # get initial model settings
        params = self.model.GetTunerParameters()
        # stash their initial values in case the user cancels tuning
        for peak in params:
            for key in peak:
                # remember that the type of the parameter gets
                # passed as well, so get the value from the tuple
                self.initial_params.append(peak[key][1])
        
        # scrollable view for model controls (since there could be many)
        scroll = wx.ScrolledWindow(self.GetPanel())
        scroll.SetScrollbars(1, 1, 1000, 1000)
        mainsizer = wx.BoxSizer(wx.VERTICAL)
        mainsizer.Add(scroll, 1, wx.EXPAND)
        self.GetPanel().SetSizer(mainsizer)

        # Buttons for finishing/canceling tuning
        btnsizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_ok = wx.Button(self.GetPanel(), label='Finish')
        btn_ok.Bind(wx.EVT_BUTTON, self.OnFinish)
        btnsizer.Add(btn_ok, 1, wx.CENTER)

        btn_cancel = wx.Button(self.GetPanel(), label='Cancel')
        btn_cancel.Bind(wx.EVT_BUTTON, self.OnCancel)
        btnsizer.Add(btn_cancel, 1, wx.CENTER)
        
        mainsizer.Add(btnsizer, 0, wx.TOP, 15)

        # Sizers for within the scrollable window itself
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        vsizer = wx.BoxSizer(wx.VERTICAL)

        # Make the controls...
        for i in range(len(params)):
            self.param_ctrls.append(dict())
            col = AutoLayoutCollapsiblePane(
                scroll,
                label='Peak {}'.format(i+1)
            )

            colpane = col.GetPane()
            grid = wx.GridSizer(2, len(params[i]), 5)  # rows, cols, gap

            # Order should be constant so no key sorting necessary
            for key in params[i]:
                # Label the control by the key
                grid.Add(wx.StaticText(colpane, label=key.title()), 1)
                # Determine what kind of field this is
                fieldtype, fieldvalue = params[i][key]

                if fieldtype == 'float':
                    ctrl = wx.SpinCtrlDouble(
                        colpane,
                        initial=fieldvalue,
                        inc=0.1,
                        min=0,
                        max=1e9 # NoneType doesn't work so b i g number instead
                    )

                    grid.Add(ctrl)
                    self.GetPanel().Bind(
                        wx.EVT_SPINCTRLDOUBLE,
                        self.OnParameterChanged,
                        ctrl
                    )

                elif fieldtype == 'int':
                    ctrl = wx.SpinCtrl(
                        colpane,
                        initial=fieldvalue,
                        inc=1,
                        min=0,
                        max=1e9 # NoneType doesn't work so b i g number instead
                    )

                    grid.Add(ctrl)
                    self.GetPanel().Bind(
                        wx.EVT_SPINCTRL,
                        self.OnParameterChanged,
                        ctrl
                    )

                else:
                    raise TypeError(
                        "Unsupported tuner type: {}".format(fieldtype))
                
                # Add the control to the collection of handles
                self.param_ctrls[i][key] = ctrl

            colpane.SetSizer(grid)
            vsizer.Add(col, 0)

            # Dividers make the controls a little easier to read
            # Don't need one after the last control though.
            if i != len(params) - 1:
                wx.StaticLine(scroll)

        # Final sizer setup
        hsizer.Add(vsizer, 1, wx.EXPAND)
        scroll.SetSizer(hsizer)

    def OnParameterChanged(self, event):
        '''
        Replot the model in response to changes in parameter values.
        '''
        newparams = []
        # Get a flat list of parameter values in order and send it to the model
        for peak in self.param_ctrls:
            for key in peak:
                newparams.append(peak[key].GetValue())

        self.model.SetTunerParameters(newparams)
        # only replot if the model is already visible
        if self.model.is_plotted:
            pub.sendMessage('Plotting.Replot')

    def OnCancel(self, event):
        '''
        Confirm whether the user wants to stop tuning. If cancelled, 
        send the original model parameters back to the object.
        '''
        with wx.MessageDialog(
            self.panel,
            "Cancel model tuning?",
            style=wx.CENTRE | wx.YES_NO | wx.CANCEL
        ) as dialog:
            if dialog.ShowModal() == wx.ID_YES:
                # pop the initial model parameters back into the model
                self.model.SetTunerParameters(self.initial_params)
                # update the plot if necessary
                if self.model.is_plotted:
                    pub.sendMessage('Plotting.Replot')
                pub.sendMessage('Data.Model.EndTune')
    
    def OnFinish(self, event):
        '''
        Confirm whether the user wants to stop tuning. If so, 
        send the new model parameters back to the object.
        '''
        with wx.MessageDialog(
            self.panel,
            "Finish model tuning?",
            style=wx.CENTRE | wx.YES_NO | wx.CANCEL
        ) as dialog:
            if dialog.ShowModal() == wx.ID_YES:
                pub.sendMessage('Data.Model.EndTune')
