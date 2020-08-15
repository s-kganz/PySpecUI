'''
Implementation of data management class. Holds all traces in memory
and implements IO functions.
'''

# GENERAL MODULES
import pandas as pd
import numpy as np
from pubsub import pub
from os.path import basename
import time
from queue import Queue, Empty

# NAMESPACE MODULES
from peaks.data.spectrum import Spectrum
from peaks.data.models import *

class DataSource(object):
    '''
    Class that handles data management and communication
    with UI elements.
    '''

    def __init__(self):
        self.traces = []
        self.trace_counter = 0

        self._ingest_queue = Queue()
        pub.subscribe(self._post_data, 'Data.Post')

    def _get_next_id(self):
        '''
        Used internally to generate unique IDs as traces
        are added.
        '''
        self.trace_counter += 1
        return self.trace_counter

    def delete_trace(self, target_id):
        '''
        Delete a trace from the manager by its ID
        '''
        pub.sendMessage('Plotting.RemoveTrace', t_id=target_id)
        for i in range(len(self.traces)):
            if self.traces[i].id == target_id:
                self.traces.pop(i)
                break
    
    def get_trace(self, t_id):
        '''
        Return trace object corresponding to the given id.
        Raises value error if no spectrum was found.
        '''
        for trace in self.traces:
            if trace.id == t_id:
                return trace
        
        raise ValueError("No trace with ID {}".format(t_id))

    def get_all_spectra(self):
        '''
        Returns a dictionary of all spectra in memory with
        ids as keys and the object as values
        '''
        return {s.id: s for s in self.traces if isinstance(s, Spectrum)}
    
    def get_all_models(self):
        '''
        Returns a dictionary of all models in memory with ids as keys and the object
        as values.
        '''
        return {m.id: m for m in self.traces if isinstance(m, Model)}

    def get_unique_name(self, name):
        '''
        Returns a modified version of name that is unique from all other traces
        in the application.
        '''
        while any(name == t.name for t in self.traces):
            if str.isnumeric(name[-1]):
                # Increment number at the end of the name
                newnum = int(name[-1]) + 1
                name = name[:-1] + str(newnum)
            else:
                name = name + '_1'
        
        return name

    def get_next_task(self):
        try:
            data = self._ingest_queue.get(block=False)
        except Empty:
            return None
        
        # Determine what type this is, add to internal manager
        # and post to the UI
        if isinstance(data, Spectrum) or isinstance(data, Model):
            # set id, add to manager, return to application
            data.id = self._get_next_id()
            self.traces.append(data)
            return data
        else:
            # unknown type
            return data
    
    def is_queue_empty(self):
        return self._ingest_queue.empty()
    
    def _post_data(self, data):
        '''
        Subscriber to new data posted by another thread. 
        '''
        self._ingest_queue.put(data)

def parse_csv(**kwargs):
    '''
    Attempt to parse a new Spectrum object and add it to the
    data in memory.

    Returns the new spectrum's trace id on a successsful call.
    '''
    # Delimiters
    delim_map = {
        "Tab": '\t',
        "Space": ' ',
        "Comma": ','
    }
    # Default read parameters
    read_opts = {
        'delimChoice': 'Comma',
        'skipCount' : 0,
        'commentChar': '#',
        'freqUnit': 'x',
        'specUnit': 'y',
        'freqCol': 0,
        'specCol': 1
    }
    read_opts.update(kwargs)
    # Attempt to read passed handle
    try:
        df = pd.read_csv(
            read_opts['file'],
            sep=delim_map[read_opts["delimChoice"]],
            skiprows=read_opts['skipCount'],
            comment=read_opts['commentChar']
        )
    except Exception as e:
        raise IOError("Reading {} failed:\n".format(read_opts['file']) + str(e))
    
    # Figure out what the shape of the df is and create a trace
    if not df.ndim < 3:
        raise IOError("Only 2-dimensional spectra are supported")
    elif df.shape[1] == 1:
        # Assume that 1-column frames are only spectral data, generate a dummy
        # frequency domain
        freq = np.linspace(0, df.shape[0], df.shape[0])
        df = pd.DataFrame({
            read_opts['freqUnit']: freq,
            read_opts['specUnit']: df.iloc[:, 0]
        })
    else:
        # Subset the df to only the frequency and spectral columns
        df = df.iloc[:, [read_opts['freqCol'], read_opts['specCol']]]
    
    # Pass remaining options to the spectrum constructor
    name = basename(read_opts['file'])
    return Spectrum(
        df,
        specunit=read_opts['specUnit'],
        frequnit=read_opts['freqUnit'],
        freqcol=read_opts["freqCol"],
        name=name
    )