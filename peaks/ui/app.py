# -- Set config options --
from kivy import Config
Config.set('graphics', 'minimum_width', '800')
Config.set('graphics', 'minimum_height', '500')
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

# -- Core kivy modules --
from kivy.app import App
from kivy.core.window import Window
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.button import Button
from kivy.uix.treeview import TreeViewNode, TreeViewLabel, TreeView
from kivy.uix.popup import Popup
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.factory import Factory
from kivy.clock import Clock
from kivy_garden.graph import MeshLinePlot, Graph

# -- Other python modules --
import numpy as np
from pubsub import pub
import random
import time
import concurrent

# -- Namespace modules --
from ..data.spectrum import Spectrum, Trace
from ..data.models import Model
from ..data.datasource import DataSource
from . import (
    dialogs, 
    parameters, 
    tabpanel, 
    treeview, 
    datagraph,
    history
)

class MyLayout(FloatLayout):
    '''
    Custom layout built off of a stack layout.
    '''
    tree = ObjectProperty(None)
    graph = ObjectProperty(None)
    status_bar = ObjectProperty(None)
    tabs = ObjectProperty(None)

class PySpecApp(App):
    def __init__(self):
        super().__init__()
        # Create data manager
        self.ds = DataSource()
        # Bind keyboard input
        Window.bind(on_key_down=self._on_key_down)
        # Create threading members
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self._thread_futures = []
        self._thread_clock_event = None
        # subscribe member functions
        pub.subscribe(self._launch_in_thread, 'Data.StartThread')

    def build(self):
        self.layout = MyLayout()
        return self.layout

    def _launch_in_thread(self, tool_run):
        '''
        Submit a new task to the other thread if it is not already
        busy. Might increase the number of threads in the future.
        '''
        self._thread_futures.append(
            (self.executor.submit(tool_run.get_call()),
            tool_run)
        )
        self.add_history_entry(tool_run)
        if self._thread_clock_event is None:
            self._thread_clock_event = Clock.schedule_interval(
                self._check_thread_status, 0.5
            )

    def _check_thread_status(self, *args):
        '''
        Scheduled on the clock when a thread is running. This function
        updates status for all threads and checks the data manager for new
        data to be ingested.
        '''
        i = 0
        while i < len(self._thread_futures):
            future, tool_run = self._thread_futures[i]
            if future.done():
                # Thread either errored out or finished, see which
                maybe_e = future.exception()
                if maybe_e is not None:
                    tool_run.status = 'Failed'
                    tool_run.append_status(str(maybe_e))
                    print('[ERROR  ]: {}'.format(str(maybe_e)))
                else:
                    tool_run.status = 'Succeeded'
                
                self._thread_futures.pop(i)
            else:
                i += 1

            self._check_new_data()

    def _check_new_data(self):
        '''
        Check for new data from the data manager. Ingest if any
        was found.
        '''
        newdata = self.ds.get_next_task()
        if newdata is not None:
            self._ingest_thread_result(newdata)
        elif len(self._thread_futures) == 0:
            Clock.unschedule(self._thread_clock_event)
            self._thread_clock_event = None

    def _ingest_thread_result(self, data):
        # Add new data from the other thread into the
        # application
        if isinstance(data, Spectrum):
            self.layout.tree.add_spectrum(data)
        elif isinstance(data, Model):
            self.layout.tree.add_model(data)
        else:
            print(data)
    
    def _do_test_button(self):
        return
        # self.layout.tabs.add_tab()
    
    def add_tuner_tab(self, tunable):
        self.layout.tabs.add_tuner(tunable)
    
    def remove_tab(self, tab):
        self.layout.tabs.remove_widget(tab)
    
    def _on_key_down(self, *args):
        _, code1, code2, text, mods = args
    
    def add_history_entry(self, tr):
        self.layout.history.add_entry(tr)

def start_application():
    PySpecApp().run()
    pub.exportTopicTreeSpec('test')