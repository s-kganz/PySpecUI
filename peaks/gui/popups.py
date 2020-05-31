'''
Derived classes of wx.Menu for context popup menus
'''
import wx

class Menu_TreeCtrlTrace(wx.Menu):
    '''
    Context menu for when a spectrum is right clicked
    in the data tab.
    '''
    def __init__(self, parent, item):
        super(Menu_TreeCtrlTrace, self).__init__()
        self.parent = parent

        # Tree item associated with this menu
        self.item = item

        item_rem = self.Append(-1, "Remove")
        item_plt = self.Append(-1, "Toggle Plotted")

        # Bind choices to the handler below
        self.Bind(wx.EVT_MENU, self.OnRemove, item_rem)
        self.Bind(wx.EVT_MENU, self.OnPlot, item_plt)

    def OnRemove(self, event):
        self.parent.RemoveTrace(self.item)
    
    def OnPlot(self, event):
        self.parent.TogglePlotted(self.item)


