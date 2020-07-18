'''
Implementation of spectral data representation.
'''
# KIVY MODULES
from kivy_garden.graph import MeshLinePlot

# GENERAL MODULES
import pandas as pd
from os.path import basename
from random import random

# NAMESPACE MODULES
from .data_helpers import Trace

__all__ = ["Spectrum", "Trace"]

class Spectrum(Trace):
    '''
    Container for pandas dataframe representing the spectrum
    and other metadata.
    '''

    def __init__(self, df, id=None, specunit="", frequnit="",
                 name="", freqcol=0, speccol=None):
        
        super(Spectrum, self).__init__()
        
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

        # Determine min/max. Spectra are immutable so this can just
        # be calculated once
        self._bounds = min(self.getx()), max(self.getx()), min(self.gety()), max(self.gety())
        self.mesh = MeshLinePlot(color=[random(), random(), random(), 1])
        self._update_mesh()

    @staticmethod
    def from_data_frame(df, id=-1, specunit="", frequnit="",
                      name="", freqcol=0, speccol=1):
        '''
        Initialize a new Spectrum object from a data frame.
        '''
        df_slice = df[[freqcol, speccol]]
        return Spectrum(df, id, specunit=specunit, frequnit=frequnit,
                        name=name, freqcol=0, speccol=1)

    @staticmethod
    def from_arrays(freq, spec, id=-1, specunit="", frequnit="",
                   name=""):
        df = pd.DataFrame({'frequency': freq, 'signal': spec})
        return Spectrum(df, id, specunit=specunit, frequnit=frequnit,
                        name=name, freqcol=0, speccol=1)

    # Trace interface implementation
    def getx(self):
        return self.data[self.freqname]

    def gety(self):
        return self.data[self.specname]

    def label(self):
        return self.name
    
    def bounds(self):
        return self._bounds
    
    def _update_mesh(self):
        '''
        Update the points in the mesh
        '''
        self.mesh.points = zip(self.getx(), self.gety())

    def get_mesh(self):
        return self.mesh

    def __str__(self):
        return self.name

        """ return "{}: {:.1f}-{:.1f} {}".format(
            self.name,
            float(min(self.data[self.freqname])),
            float(max(self.data[self.freqname])),
            self.frequnit
        ) """
