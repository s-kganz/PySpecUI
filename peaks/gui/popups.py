'''
Derived classes of wx.Menu for context popup menus
'''
# GENERAL MODULES
from pubsub import pub

# WX MODULES
import wx

# NAMESPACE MODULES
from peaks.data.models import Model
from peaks.data.spec import Spectrum

class Menu_TreeCtrlTrace(wx.Menu):
    '''
    Context menu for when a spectrum is right clicked
    in the data tab.
    '''
    def __init__(self, parent, item, data):
        super(Menu_TreeCtrlTrace, self).__init__()
        self.parent = parent # Hook to the DataTab object that spawned this menu

        # Tree item and python object associated with this menu
        self.item = item
        self.data = data

        # Actions available for all traces
        item_rem = self.Append(-1, "Remove")
        item_plt = self.Append(-1, "Toggle Plotted")

        # Actions only available for models
        if issubclass(type(self.data), Model):
            item_mod = self.Append(-1, 'Tune Model')
            self.Bind(wx.EVT_MENU, self.OnTune, item_mod)

        # Bind choices to the handler below
        self.Bind(wx.EVT_MENU, self.OnRemove, item_rem)
        self.Bind(wx.EVT_MENU, self.OnPlot, item_plt)

    def OnRemove(self, event):
        self.parent.RemoveTrace(self.item)
    
    def OnPlot(self, event):
        self.parent.TogglePlotted(self.item)

    def OnTune(self, event):
        pub.sendMessage('Data.Model.Tune', model=self.data)
        