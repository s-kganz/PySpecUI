'''
Utility functions for working with spectra.
'''
import numpy as np

def subset(arr, lower, upper):
    '''
    Returns a mask of arr, where true elements represent values x
    where lower < x < upper.
    '''
    return np.logical_and(arr > lower, arr < upper)