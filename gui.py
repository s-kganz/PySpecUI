'''
This file includes implementation of derived classes for building
the application interface.
'''

import wx
import time
import asyncio
from wxasync import AsyncBind, WxAsyncApp, StartCoroutine
from wxmplot import PlotPanel

class LoadDialog(wx.Dialog):
    '''
    Dialog window containing controls for loading a new data source.
    '''
    def __init__(self, parent=None):
        super(LoadDialog, self).__init__(self, parent)
        self.InitUI()
    
    def InitUI(self):
        pass


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
        super(Layout, self).__init__(parent, title=title)
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
        with wx.FileDialog(self, "Open XYZ file", wildcard="All files (*)|*.*",
                        style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:

            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return     # the user changed their mind

            # Proceed loading the file chosen by the user
            pathname = fileDialog.GetPath()
            try:
                print("Load!")
            except IOError:
                wx.LogError("Cannot open file '%s'." % newfile)

    async def SlowFunc(self, e):
        '''
        Dummy function to test status bar updating asynchronously
        '''
        self.status.PushStatusText("Working...")
        await asyncio.sleep(5)
        self.status.PopStatusText()


class App(WxAsyncApp):
    def OnInit(self):
        self.layout = Layout(None, title='Layout test')
        self.layout.Show()
        return True
