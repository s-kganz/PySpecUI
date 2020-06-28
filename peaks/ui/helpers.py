from kivy.uix.treeview import TreeViewNode
from kivy.uix.button import Button

class TreeViewButton(Button, TreeViewNode):
    '''
    Helper widget to add buttons to a tree view.
    '''