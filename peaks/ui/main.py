# -- Set config options --
from kivy import Config
Config.set('graphics', 'minimum_width', '800')
Config.set('graphics', 'minimum_height', '500')
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

# -- Core kivy modules --
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.button import Button
from kivy.uix.treeview import TreeViewNode, TreeViewLabel, TreeView
from kivy.uix.popup import Popup
from kivy.factory import Factory
from kivy.clock import Clock
from kivy_garden.graph import MeshLinePlot, Graph

# -- Other python modules --
import numpy as np
from pubsub import pub
import random
import concurrent

# -- Namespace modules --
from peaks.data.spectrum import Spectrum, Trace
from peaks.data.datasource import DataSource
import peaks.ui.dialogs as dialogs

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

class MyLayout(FloatLayout):
    '''
    Custom layout built off of a stack layout.
    '''
    tree = ObjectProperty(None)
    graph = ObjectProperty(None)
    status_bar = ObjectProperty(None)

    def __init__(self, *args, **kwargs):
        super(MyLayout, self).__init__(*args, **kwargs)
        pub.subscribe(self.add_plot, 'Plot.AddPlot')
        pub.subscribe(self.remove_plot, 'Plot.RemovePlot')
        pub.subscribe(self.clear_all_plots, 'Plot.RemoveAll')

    def clear_all_plots(self):
        '''
        Remove all meshes in the plotting window.
        '''
        meshes = self.graph.plots.copy()
        for mesh in meshes:
            self.graph.remove_plot(mesh)
            
    def add_plot(self, trace=None, xmax=0, ymax=0):
        '''
        Add a new trace object to the plot, update graph limits to include
        the entirety of the new data.
        '''
        self.graph.xmax = max(xmax, self.graph.xmax)
        self.graph.ymax = max(ymax, self.graph.ymax)

        self.graph.add_plot(trace)
    
    def remove_plot(self, trace=None):
        '''
        Remove a trace object from the plot.
        '''
        self.graph.remove_plot(trace)
    
    def zoom_out(self):
        '''
        Zoom out the plot by a factor of two.
        '''
        self.graph.xmax *= 2
        self.graph.ymax *= 2
    
    def zoom_in(self):
        '''
        Zoom in the plot by a factor of two
        '''
        self.graph.ymax /= 2
        self.graph.xmax /= 2
        

class PySpecApp(App):
    def __init__(self):
        super().__init__()
        self.ds = DataSource()
        self.executor = concurrent.futures.ThreadPoolExecutor()
        self._thread_future = None
        self._thread_clock_event = None
        # subscribe member functions
        pub.subscribe(self.load_csv, 'Data.LoadCSV')

    def build(self):
        self.layout = MyLayout()
        return self.layout

    def _launch_in_thread(self, caller):
        '''
        Submit a new task to the other thread if it is not already
        busy. Might increase the number of threads in the future.
        '''
        if self._thread_future is None or not self._thread_future.running():
            self._thread_future = self.executor.submit(
                caller
            )
            self._thread_clock_event = Clock.schedule_interval(
                self._check_thread_status, 0.5
            )
        else:
            print("Another thread is currently running!")

    def _check_thread_status(self, *args):
        '''
        Scheduled on the clock when a thread is running. Check if the
        thread finished and ingests new data if available.
        '''
        if not self._thread_future.done(): return
        else:
            Clock.unschedule(self._thread_clock_event)
            # Check if the thread errored out
            # TODO handle errors gracefully
            maybe_e = self._thread_future.exception()
            if maybe_e is not None:
                raise maybe_e
            else:
                self._ingest_thread_result(self._thread_future.result())

    def _ingest_thread_result(self, data):
        # Add new data from the other thread into the
        # application
        if isinstance(data, Spectrum):
            self.layout.tree.add_spectrum(data)
        else:
            print(data)

    def load_csv(self, options={}):
        '''
        Wrapper around the relevant function in DataSource
        '''
        self._launch_in_thread(lambda: self.ds.add_trace_from_csv(options))
        
if __name__ == '__main__':
    PySpecApp().run()
    pub.exportTopicTreeSpec('test')