'''
Implementation of data management class. Holds all traces in memory
and implements IO functions.
'''

# GENERAL MODULES
import pandas as pd
from pubsub import pub
from os.path import basename

# WX MODULES
import wx

# NAMESPACE MODULES
from .spec import Spectrum
from .models import *

class DataSource(object):
    '''
    Class that handles data management and communication
    with UI elements.
    '''

    def __init__(self):
        self.traces = []
        self.trace_counter = 0
        
        self.delim_map = {
            "Tab": '\t',
            "Space": ' ',
            "Comma": ','
        }

        # Subscribe member functions
        pub.subscribe(self.AddTraceFromCSV, 'Data.LoadCSV')
        pub.subscribe(self.AddModel, 'Data.AddModel')
        pub.subscribe(self.DeleteTrace, 'Data.DeleteTrace')

    def GetNextId(self):
        '''
        Used internally to generate unique IDs as traces
        are added.
        '''
        self.trace_counter += 1
        return self.trace_counter

    def AddTraceFromCSV(self, file, options = {}):
        '''
        Attempt to parse a new Spectrum object and add it to the
        data in memory.

        Returns the new spectrum's trace id on a successsful call.
        '''
        # Default read parameters
        read_opts = {
            'delimChoice': 'Comma',
            'skipCount' : 0,
            'commentChar': '#',
            'freqUnit': 'x',
            'specUnit': 'y',
            'freqColInd': 0
        }
        read_opts.update(options)
        # Attempt to read passed handle
        try:
            df = pd.read_csv(
                file,
                sep=self.delim_map[read_opts["delimChoice"]],
                header=0,
                skiprows=read_opts['skipCount'],
                comment=read_opts['commentChar']
            )
        except Exception as e:
            raise IOError("Reading {} failed:\n".format(file) + str(e))
        
        # Figure out what the shape of the df is and create traces
        # TODO add support for reading many spectra from a csv at once
        if not df.shape[1] == 2:
            pub.sendMessage(
                'Logging.Error', 
                caller='DataSource.AddTraceFromCSV', 
                msg="Reading multi-column spectra is not supported")
            return
        if not df.ndim < 3:
            pub.sendMessage(
                'Logging.Error', 
                caller='DataSource.AddTraceFromCSV', 
                msg="Reading dataframe with more than 2 dimensions is not supported"
            )
            return
        
        # Pass remaining options to the spectrum constructor
        name = basename(file)
        spec_id = self.GetNextId()
        self.traces.append(Spectrum(
            df,
            spec_id,
            specunit=read_opts['specUnit'],
            frequnit=read_opts['freqUnit'],
            freqcol=read_opts["freqColInd"],
            name=name
        ))

        # Pass the Spectrum to the data tab so it shows up in the UI
        pub.sendMessage(
            'UI.Tree.AddTrace', 
            trace=self.traces[len(self.traces)-1], 
            type='spec'
        )
        return spec_id

    def AddModel(self, model):
        '''
        Add a newly created model to the internal manager and
        the data tab.
        '''
        new_id = self.GetNextId()
        model.id = new_id
        self.traces.append(model)
        pub.sendMessage(
            'UI.Tree.AddTrace', 
            trace=self.traces[len(self.traces)-1], 
            type='model'
        )
        return new_id

    def DeleteTrace(self, target_id):
        '''
        Delete a trace from the manager by its ID
        '''
        pub.sendMessage('Plotting.RemoveTrace', t_id=target_id)
        for i in range(len(self.traces)):
            if self.traces[i].id == target_id:
                self.traces.pop(i)
                break
    
    def GetTraceByID(self, id):
        '''
        Return spectrum object corresponding to the given id. Returns
        None if no specturm was found
        '''
        for trace in self.traces:
            if trace.id == id:
                return trace
        
        pub.sendMessage(
            'Logging.Error',
            caller='DataSource.GetTraceByID',
            msg="No trace with ID {}".format(id)
        )
