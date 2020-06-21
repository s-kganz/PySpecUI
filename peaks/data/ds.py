'''
Implementation of data management class. Holds all traces in memory
and implements IO functions.
'''

# GENERAL MODULES
import pandas as pd
import numpy as np
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

    def AddTraceFromArrays(self, spec, freq, options = {}):
        '''
        Internal function to create a trace object from numpy arrays
        '''
        raise NotImplementedError("AddTraceFromArrays not implemented yet")

    def AddTraceFromDataFrame(self, df, options = {}):
        '''
        Create a function from a pandas dataframe.
        '''
        raise NotImplementedError("AddTraceFromDataFrame not implemented yet")

    def AddManyFromDataFrame(self, df, options = {}):
        '''
        Create many Spectrum objects from a pandas dataframe.
        '''
        raise NotImplementedError("AddManyFromDataFrame not implemented yet.")

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
            'freqColInd': 0,
            'specColInd': 1
        }
        read_opts.update(options)
        # Attempt to read passed handle
        try:
            df = pd.read_csv(
                file,
                sep=self.delim_map[read_opts["delimChoice"]],
                skiprows=read_opts['skipCount'],
                comment=read_opts['commentChar']
            )
        except Exception as e:
            raise IOError("Reading {} failed:\n".format(file) + str(e))
        
        # Figure out what the shape of the df is and create a trace
        if not df.ndim < 3:
            pub.sendMessage(
                'Logging.Error', 
                caller='DataSource.AddTraceFromCSV', 
                msg="Reading dataframe with more than 2 dimensions is not supported"
            )
            return
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
            df = df.iloc[:, [read_opts['freqColInd'], read_opts['specColInd']]]

        
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

    def AddManyFromCSV(self, file, options = {}):
            '''
            Parse several Spectrum objects from one delimited file
            and add them to memory.

            Returns the min and max of the new objects' ids.
            '''
            raise NotImplementedError("AddManyFromCSV not implemented yet")
        
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
    
    def GetTraceByID(self, t_id):
        '''
        Return spectrum object corresponding to the given id. Returns
        None if no specturm was found
        '''
        for trace in self.traces:
            if trace.id == t_id:
                return trace
        
        raise ValueError("No trace with ID {}".format(t_id))