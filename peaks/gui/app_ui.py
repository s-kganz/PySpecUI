'''
Implementation of the high-level application UI and startup
function.
'''

# GENERAL MODULES
from asyncio import get_event_loop
from pubsub import pub

# WX MODULES
import wx
from wxasync import StartCoroutine

# NAMESPACE MODULES
from peaks.data.ds import DataSource
from .subpanels import *

class Layout(wx.Frame):
    '''
    Main frame of the application.
    '''

    def __init__(self, parent, title, datasrc=None):
        super(Layout, self).__init__(parent, title=title, size=(1000, 600))
        self.datasrc = datasrc
        self.InitUI()
        self.Centre()
        pub.subscribe(self.SetStatus, 'UI.SetStatus')
        pub.subscribe(self.LogError, 'Logging.Error')

    def InitUI(self):
        '''
        Create widgets.
        '''
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
        def loadFunc(x): return pub.sendMessage(
            'Dialog.Run', D=DialogLoad, data=dict())
        self.Bind(wx.EVT_MENU, loadFunc, loadItem)
        # Dummy option to test status bar
        statItem = dataMenu.Append(wx.ID_ANY, 'Compute', 'Think really hard')
        self.Bind(wx.EVT_MENU, lambda x: StartCoroutine(
            self.SlowFunc(x), self), statItem)

        # Fitting submenu
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
        self.tab_pane = TabPanel(splitter, self.datasrc)

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

        data = {
            'names': names,
            'datasrc': self.datasrc
        }
        pub.sendMessage('Dialog.Run', D=DialogGaussModel, data=data)

    def SetStatus(self, text):
        '''
        Set the statusbar text.
        '''
        self.status.SetStatusText(text)

    def LogError(self, caller, msg):
        '''
        Raise an error dialog.

        caller: The object that raised the error (as a string)
        msg: error information
        '''
        s = '[{}]: {}'.format(caller, msg)
        wx.LogError(s)

    async def SlowFunc(self, e):
        '''
        Dummy function to test status bar updating asynchronously
        '''
        self.status.PushStatusText("Working...")
        await asyncio.sleep(5)
        self.status.PopStatusText()


class App(WxAsyncApp):
    '''
    Overall application class. Inherits WxAsyncApp
    to allow for asynchronous execution.
    '''

    def __init__(self, datasrc=None):
        self.datasrc = datasrc
        super(App, self).__init__()

    def OnInit(self):
        '''
        Simply build the layout and return.
        '''
        self.layout = Layout(None, title='PyPeaks', datasrc=self.datasrc)
        self.layout.Show()
        return True


def start_app():
    '''
    Main driver function.
    '''
    ds = DataSource()
    app = App(datasrc=ds)
    pub.exportTopicTreeSpec('test')
    loop = get_event_loop()
    loop.run_until_complete(app.MainLoop())
