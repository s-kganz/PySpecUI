'''
Implementation of data manager class for handling spectra.
'''
import pandas as pd

class Spectrum(object):
    '''
    Container for pandas dataframe representing the spectrum
    and other metadata.
    '''
    def __init__(self, df, freqcol=0, speccol=1):
        self.data = df.copy() 
        self.specname = df.columns[speccol]
        self.freqname = df.columns[freqcol]
        
        self.specunits = "Unknown"
        self.frequnits = "Unknown"

        self.desc = "A spectrum."


class DataSource(object):
    '''
    Class that handles data management and communication
    with UI elements.
    '''

    def __init__(self, app=None):
        self.app = app # Connection to the UI
        self.traces = []

        self.mode = 'ui' if self.app else 'repl'
        self.delim_map = {
            "Tab": '\t',
            "Space": ' ',
            "Comma": ','
        }

    def addTraceFromCSV(self, file, options = {}):
        '''
        Attempt to parse a new Spectrum object and add it to the
        data in memory.

        Returns the index of the trace on a successful call.
        '''
        # Attempt to read passed handle
        try:
            df = pd.read_csv(file)
        except Exception as e:
            raise IOError("Reading {} failed:\n".format(file) + str(e))
        
        # Figure out what the shape of the df is and create traces
        # TODO add support for reading many spectra from a csv at once
        if not df.shape[1] == 2:
            raise IOError("Reading multi-column spectra is not supported")
        if not df.ndim < 3:
            raise IOError("Reading dataframe with more than 2 dimensions is not supported")
        # Assume that the first column is the frequency column and the second
        #   is the spectral data

        self.traces.append(Spectrum(df))
        return len(self.traces) - 1 # last index



