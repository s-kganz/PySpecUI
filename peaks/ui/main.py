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
        self.text = 'd{}ta'.format('a' * random.choice(range(1, 25)))
    
    def send_plot_message(self):
        if self.check.active:
            pub.sendMessage('Plot.AddPlot', trace=self.plot)
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

    def _create_fake_data(self, n_points=1000):
        x = np.linspace(0, 100, num=n_points)
        y = np.sin(x) * 3 + np.random.normal(0, 1, n_points)
        s = Spectrum.FromArrays(x, y)
        self.add_spectrum(s)

    def add_spectrum(self, s):
        self.add_node(TreeViewPlottable(s), parent=self.headers[0])

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

    def create_random_plot(self):
        plot = MeshLinePlot(color=[1, 0, 0, 1])
        x = np.linspace(1, 100, num=100)
        y = np.sin(x) * 2 + np.random.normal(0, 1, len(x))
        plot.points = [(a,b) for (a,b) in zip(x, y)]
        self.meshes.append(plot)

        self.graph.add_plot(plot)

    def clear_all_plots(self):
        meshes = self.graph.plots.copy()
        for mesh in meshes:
            self.graph.remove_plot(mesh)
            
    def add_plot(self, trace=None):
        '''
        Add a new trace object to the plot
        '''
        self.graph.add_plot(trace)
    
    def remove_plot(self, trace=None):
        '''
        Remove a trace object from the plot.
        '''
        self.graph.remove_plot(trace)
        

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
        layout = MyLayout()
        return layout

    def _launch_in_thread(self, caller):
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
        if not self._thread_future.done(): return
        else:
            Clock.unschedule(self._thread_clock_event)
            e = self._thread_future.exception()
            if e is not None:
                raise e
            else:
                print(self._thread_future.result())

    def _ingest_thread_result(self, data):
        if isinstance(data, Spectrum):
            self.tree.add_spectrum(data)
        else:
            print(data)

    def load_csv(self, options={}):
        self._launch_in_thread(lambda: self.ds.add_trace_from_csv(options))
        
    

if __name__ == '__main__':
    PySpecApp().run()
    pub.exportTopicTreeSpec('test')