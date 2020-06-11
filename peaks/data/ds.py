
import pandas as pd
from pubsub import pub
import wx

from os.path import basename
from peaks.data.spec import Spectrum
from peaks.data.models import ModelGauss

__all__ = ["DataSource"]

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
        pub.subscribe(self.DeleteTrace, 'Data.DeleteTrace')

    def GetNextId(self):
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
            'sep': 'Comma',
            'skiprows' : 0,
            'comment': '#',
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
            wx.LogError("Reading multi-column spectra is not supported")
            return
        if not df.ndim < 3:
            wx.LogError("Reading dataframe with more than 2 dimensions is not supported")
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
        pub.sendMessage('UI.Tree.AddTrace', trace=self.traces[len(self.traces)-1], type='spec')

    def CreateGaussModel(self, spec_id, **kwargs):
        '''
        Create a Gaussian model of the passed spectrum object.

        Returns the model's trace id on a successful fit. Otherwise
        returns None.
        '''
        # Construct the model object and fit it
        mod_id = self.GetNextId()
        mg = ModelGauss(self.GetTraceByID(spec_id), mod_id)
        
        if not mg.Fit(mg.ParamGuess(**kwargs)):
            return None
        
        # On a successful fit, add the new model to memory
        self.traces.append(mg)
        return mod_id

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
        
        return None
