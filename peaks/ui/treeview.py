from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.treeview import TreeViewNode, TreeViewLabel, TreeView
from kivy.uix.boxlayout import BoxLayout
from kivy_garden.graph import Graph, MeshLinePlot

import random
from pubsub import pub
import numpy as np

from peaks.data.spectrum import Spectrum, Trace

class TreeViewPlottable(TreeViewNode, BoxLayout):
    '''
    Item in a TreeView that holds an object.
    '''
    check = ObjectProperty(None) # reference to the check box
    text = StringProperty(None)
    plot = ObjectProperty(None)

    def __init__(self, obj: Trace, *args, **kwargs):
        super(TreeViewPlottable, self).__init__(*args, **kwargs)
        self.trace = obj
        # Make a plot
        self.plot = MeshLinePlot(color=[random.random(), random.random(), random.random(), 1])
        self.plot.points = zip(self.trace.getx(), self.trace.gety())
        self.text = str(obj)
    
    def send_plot_message(self):
        '''
        Called when the checkbox status changes. If the checkbox
        became active, send the MeshLinePlot to the plot window. Otherwise,
        remove the plot from the window.
        '''
        if self.check.active:
            # The bounds of the graph on the y axis a little fuzzy, so padding
            # 10% ensures all data will be in view.
            xmax, ymax = int(self.trace.getx().max()), \
                         int(self.trace.gety().max() * 1.1)
            pub.sendMessage('Plot.AddPlot', trace=self.plot, xmax=xmax, ymax=ymax)
        else:
            pub.sendMessage('Plot.RemovePlot', trace=self.plot)
    
    def on_touch_down(self, touch):
        if not super().on_touch_down(touch) and touch.button == 'right':
            print('oof')

class DataTreeView(TreeView):
    '''
    Custom tree view for holding onto spectral data
    '''
    headers = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._populate_nodes()
        pub.subscribe(self.uncheck_all, 'Plot.RemoveAll')

    def _create_fake_data(self, n_points=1000):
        '''
        Test function : make a simple sinusoid and add it to the
        tree.
        '''
        x = np.linspace(0, 100, num=n_points)
        y = np.sin(x) * 3 + np.random.normal(0, 1, n_points)
        s = Spectrum.FromArrays(x, y)
        self.add_spectrum(s)

    def add_spectrum(self, s):
        '''
        Add a spectrum to the tree.
        '''
        self.add_node(TreeViewPlottable(s), parent=self.headers[0])
    
    def add_model(self, m):
        '''
        Add a model to the tree.
        '''
        self.add_node(TreeViewPlottable(m), parent=self.headers[1])

    def uncheck_all(self):
        '''
        Uncheck all plottable nodes.
        '''
        for n in self.iterate_all_nodes():
            if isinstance(n, TreeViewPlottable):
                n.check.active = False

    def _populate_nodes(self):
        '''
        Set up primary headers.
        '''
        for header in ["Spectra", "Models", "Tool Chains"]:
            node = self.add_node(TreeViewLabel(text=header))
            self.headers.append(node)