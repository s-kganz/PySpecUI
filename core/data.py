'''
Implementation of data manager class and underlying spectrum
representation.
'''
import pandas as pd
from os.path import basename

class Spectrum(object):
    '''
    Container for pandas dataframe representing the spectrum
    and other metadata.
    '''
    def __init__(self, df, id, specunit="", frequnit="", 
                 name="", freqcol=0, speccol=None):
        # Assign this spectrum an ID
        self.id = id

        # Assume that the passed df only has two columns
        # TODO refactor to allow multi-column support.
        speccol = 1 if freqcol == 0 else 0

        self.data = df.copy() 
        self.specname = df.columns[speccol]
        self.freqname = df.columns[freqcol]
        
        self.specunit = specunit
        self.frequnit = frequnit

        self.name = name
        self.is_plotted = False

    def getx(self):
        return self.data[self.freqname]
    
    def gety(self):
        return self.data[self.specname]

    def __str__(self):
        return "{}: {}-{} {}".format(
            self.name,
            min(self.data[self.freqname]),
            max(self.data[self.freqname]),
            self.frequnit
        )

class DataSource(object):
    '''
    Class that handles data management and communication
    with UI elements.
    '''

    def __init__(self, app=None):
        self.app = app # Connection to the UI
        self.traces = []
        self.trace_counter = 0

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
            df = pd.read_csv(
                file,
                sep=self.delim_map[options["delimChoice"]],
                header=0,
                skiprows=options['skipCount'],
                comment=options['commentChar']
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
        self.traces.append(Spectrum(
            df,
            self.trace_counter,
            specunit=options['specUnit'],
            frequnit=options['freqUnit'],
            freqcol=options["freqColInd"],
            name=name
        ))
        self.trace_counter += 1
        return len(self.traces) - 1 # last index

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
        for spec in self.traces:
            if spec.id == id:
                return spec
        
        return None


