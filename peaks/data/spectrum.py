'''
Implementation of spectral data representation.
'''
# KIVY MODULES
from kivy_garden.graph import MeshLinePlot

# GENERAL MODULES
import pandas as pd
from os.path import basename
from random import random
from copy import deepcopy

# NAMESPACE MODULES
from .data_helpers import Trace

__all__ = ["Spectrum", "Trace"]

class Spectrum(Trace):
    '''
    Container for pandas dataframe representing the spectrum
    and other metadata.
    '''

    def __init__(self, df, id=None, specunit="", frequnit="",
                 name="", freqcol=0, speccol=1):
        
        super(Spectrum, self).__init__()
        
        # Assign this spectrum an ID
        self.id = id

        self.specname = df.columns[speccol]
        self.freqname = df.columns[freqcol]
        self.data = df.iloc[:, [speccol, freqcol]].reset_index(drop=True).copy()

        self.specunit = specunit
        self.frequnit = frequnit

        self.name = name
        self.is_plotted = False
        self.history = []

        # Determine min/max. Spectra are immutable so this can just
        # be calculated once
        self._bounds = min(self.getx()), max(self.getx()), min(self.gety()), max(self.gety())
        # The mesh should not be instantiated unless in a graphics context. Otherwise the kernel
        # dies. No idea why.
        self._color = [random(), random(), random()]
        self.mesh = None
        self._update_mesh()

    @staticmethod
    def from_data_frame(df, id=-1, specunit="", frequnit="",
                      name="", freqcol=0, speccol=1):
        '''
        Initialize a new Spectrum object from a data frame.
        '''
        df_slice = df.iloc[:, [freqcol, speccol]].reset_index(drop=True).copy()

        return Spectrum(df_slice, id, specunit=specunit, frequnit=frequnit,
                        name=name, freqcol=0, speccol=1)

    @staticmethod
    def from_arrays(freq, spec, id=-1, specunit="", frequnit="",
                   name=""):
        df = pd.DataFrame({'frequency': freq, 'signal': spec})
        return Spectrum(df, id, specunit=specunit, frequnit=frequnit,
                        name=name, freqcol=0, speccol=1)

    # Mutators
    def apply_spec(self, func, *args, **kwargs):
        '''
        Apply a function to the spectral data of this object, returning a new
        object with the function applied.
        '''
        if not callable(func):
            raise ValueError('Spectrum.apply_spec: func must be a callable!')
        new_spec = func(self.gety().copy(), *args, **kwargs)
        new_s = Spectrum.from_arrays(
            self.getx().copy(), 
            new_spec, 
            id=-1, 
            specunit=self.specunit,
            frequnit=self.frequnit,
            name=self.name
        )
        new_s.history = deepcopy(self.history)
        new_s.history.append({
            'type': 'spec',
            'callable': func,
            'args': args,
            'kwargs': kwargs
        })
        return new_s
    
    def apply_freq(self, func, *args, **kwargs):
        '''
        Apply a function to the frequency data of this object, returning a new
        object with the function applied.
        '''
        if not callable(func):
            raise ValueError('Spectrum.apply_freq: func must be a callable!')
        new_freq = func(self.getx().copy(), *args, **kwargs)
        new_s = Spectrum.from_arrays(
            new_freq, 
            self.gety().copy(), 
            id=-1, 
            specunit=self.specunit,
            frequnit=self.frequnit,
            name=self.name
        )
        new_s.history = deepcopy(self.history)
        new_s.history.append({
            'type': 'freq',
            'callable': func,
            'args': args,
            'kwargs': kwargs
        })
        return new_s

    def apply_spec_freq(self, func, *args, **kwargs):
        '''
        Apply a function to the frequency and spectral data of this object, returning a new
        object with the function applied.
        '''
        if not callable(func):
            raise ValueError('Spectrum.apply_spec_freq: func must be a callable!')
        new_freq, new_spec = func(self.getx().copy(), self.gety().copy(), *args, **kwargs)
        new_s = Spectrum.from_arrays(
            new_freq, 
            new_spec, 
            id=-1, 
            specunit=self.specunit,
            frequnit=self.frequnit,
            name=self.name
        )
        new_s.history = deepcopy(self.history)
        new_s.history.append({
            'type': 'spec_freq',
            'callable': func,
            'args': args,
            'kwargs': kwargs
        })
        return new_s

    def apply_object(self, func, *args, **kwargs):
        '''
        Apply a function to this object and returns the resulting
        Spectrum.
        '''
        if not callable(func):
            raise ValueError('Spectrum.apply_object: func must be a callable!')
        
        new_obj = func(Spectrum.from_arrays(
            self.getx(),
            self.gety(),
            id=-1,
            specunit=self.specunit,
            frequnit=self.frequnit,
            name=self.name
        ), *args, **kwargs)

        new_obj.history = deepcopy(self.history)
        new_obj.history.append(
            {
                'type': 'object',
                'callable': func,
                'args': args,
                'kwargs': kwargs
            }
        )

        return new_obj

    def apply_history(self, other):
        '''
        Returns the spectrum object resulting from running all
        apply_* calls in another spectrum's history.
        '''
        ret = self
        for entry in other.history:
            if entry['type'] == 'spec':
                ret = ret.apply_spec(entry['callable'], *entry['args'], **entry['kwargs'])
            elif entry['type'] == 'freq':
                ret = ret.apply_freq(entry['callable'], *entry['args'], **entry['kwargs'])
            elif entry['type'] == 'spec_freq':
                ret = ret.apply_spec_freq(entry['callable'], *entry['args'], **entry['kwargs'])
            elif entry['type'] == 'object':
                ret = ret.apply_object(entry['callable'], *entry['args'], **entry['kwargs'])
            else:
                raise ValueError('Spectrum.apply_history: Unrecognized spectrum operation'
                                 ': {}'.format(entry['type']))
        return ret

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
        if self.mesh is not None:
            self.mesh.points = zip(self.getx(), self.gety())

    def get_mesh(self):
        if self.mesh is None:
            self.mesh = MeshLinePlot(color=self._color)
            self.mesh.points = zip(self.getx(), self.gety())
        return self.mesh

    def __str__(self):
        return self.name

        """ return "{}: {:.1f}-{:.1f} {}".format(
            self.name,
            float(min(self.data[self.freqname])),
            float(max(self.data[self.freqname])),
            self.frequnit
        ) """
