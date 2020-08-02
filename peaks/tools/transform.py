'''
Functions for transforming spectra. I.e. rescaling, converting absorbance to transmittance, etc.
'''
import numpy as np

def to_absorbance(y):
    '''
    Convert the signal in y to values of absorbance, assuming that the input
    is in transmittance.
    '''
    return np.log10(np.reciprocal(y))

def to_transmittance(y):
    '''
    Convert the signal in y to values of transmittance, assuming that the input
    is in transmittance.
    '''
    return np.power(10, -y)

def rescale(y, min, max):
    '''
    Rescale the signal in y such that its minimum and maximum values are
    min and max, respectively.
    '''
    return np.interp(y, (y.min(), y.max()), (min, max))
