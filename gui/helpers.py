'''
Mixins and other classes derived from stock wxpython controls
'''

import os

import wx
from wx.lib.mixins.treemixin import DragAndDrop

class DragAndDropTree(wx.TreeCtrl, DragAndDrop):
    '''
    Mixin class to enable drag and drop with the stock TreeCtrl.
    '''
    def __init__(self, parent, datasrc, style=wx.TR_DEFAULT_STYLE):
        self.datasrc = datasrc
        super(DragAndDropTree, self).__init__(parent, style=style)

    def OnDrop(self):
        '''
        Dropping one item on top of another is not meaningful, so just return.
        '''
        return

class DirTreeCtrl(wx.TreeCtrl):
    '''
    A window showing files/folder in the current working directory. Implementation comes from:
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

        # Bind double clicking an item to trying to read that file
        self.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.OnDblClick)

    def setwd(self, newdir):
        self.dir = newdir
        self.DeleteAllItems()
        ids = {newdir : self.AddRoot(newdir, self.folderidx)}
        self.SetItemHasChildren(ids[newdir])
 
        for (dirpath, dirnames, filenames) in os.walk(newdir):
            for dirname in sorted(dirnames):
                fullpath = os.path.join(dirpath, dirname)
                ids[fullpath] = self.AppendItem(ids[dirpath], dirname, self.folderidx)
                 
            for filename in sorted(filenames):
                self.AppendItem(ids[dirpath], filename, self.fileidx)
        
        self.Expand(self.GetRootItem())
    
    def OnDblClick(self, event):
        act_item = event.GetItem()
        # If the item is a folder (has children), expand/collapse it. Otherwise, try and read it.
        if self.GetChildrenCount(act_item) > 0:
            # Expand if collapsed, otherwise collapse
            if self.IsExpanded(act_item): self.Collapse(act_item)
            else: self.Expand(act_item)
        else:
            # Walk up the tree until the root is reached to get all folders in the path
            folders = []
            walker = act_item
            while walker.IsOk():
                folders.append(self.GetItemText(walker))
                walker = self.GetItemParent(walker)
            
            abspath = os.path.join(*folders[::-1])
            
            # Normally this function takes an event object so we pass None here
            wx.GetTopLevelParent(self).LoadData(None, path=abspath)