'''
Functions for computing baselines of spectra.
'''
import numpy as np
from .util import subset

def polynomial_baseline(x, y, left_bound, right_bound, degree=1, invert=False):
    '''
    Return a numpy array representing the baseline of y, calculated by fitting
    a polynomial of the given degree to the region of y given by left_bound < x < right_bound.

    If invert is True, the mask used to subset the array is inverted. That is, if invert is true
    values of y outside of the region are used to fit the baseline.
    '''
    mask = subset(x, left_bound, right_bound)
    if invert: mask = ~mask

    baseline_x = x[mask]
    baseline_y = y[mask]

    return np.polyval(np.polyfit(baseline_x, baseline_y, degree), x)