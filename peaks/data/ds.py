
import pandas as pd
from os.path import basename
from peaks.data.spec import Spectrum
from peaks.data.models import ModelGauss

__all__ = ["DataSource"]

class DataSource(object):
    '''
    Class that handles data management and communication
    with UI elements.
    '''

    def __init__(self, app=None):
        self.app = app # Connection to the UI
        self.traces = []
        self.trace_counter = 0
        
        self.delim_map = {
            "Tab": '\t',
            "Space": ' ',
            "Comma": ','
        }

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
            raise IOError("Reading multi-column spectra is not supported")
        if not df.ndim < 3:
            raise IOError("Reading dataframe with more than 2 dimensions is not supported")
        
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
        return spec_id

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
        for i in range(len(self.traces)):
            if self.traces[i].id == target_id:
                self.traces.pop(i)
                return True
        
        return False
    
    def GetTraceByID(self, id):
        '''
        Return spectrum object corresponding to the given id. Returns
        None if no specturm was found
        '''
        for trace in self.traces:
            if trace.id == id:
                return trace
        
        return None
