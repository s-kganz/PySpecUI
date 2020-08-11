'''
Functions for computing baselines of spectra.
'''
import scipy.signal as signal
from scipy.signal import savgol_filter
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

def polynomial_detrend(x, y, left_bound, right_bound, degree=1, invert=False):
    '''
    Return the detrended x and y arrays after subtracting the baseline resulting from a 
    call to polynomial_baseline.
    '''
    return x, y - polynomial_baseline(
        x, y, 
        left_bound, right_bound, 
        degree=degree, invert=invert)

def boxcar_smooth(y, winlen):
    '''
    Return the moving average of the input array, with winlen
    defining the width of the window.
    '''
    # Normalize sum of the window
    window = signal.windows.boxcar(winlen) / winlen

    return np.convolve(y, window, mode='same')

def triangular_smooth(y, winlen):
    '''
    Return the convolution of the input array with a triangular
    window of width winlen.
    '''
    window = signal.windows.triang(winlen)
    window /= np.sum(window)

    return np.convolve(y, window, mode='same')

def gaussian_smooth(y, winlen, p, sigma):
    '''
    Return the convolution of the input array with a gaussian
    window of width winlen, and shape parameters p and sigma.

    Note that p in this case is not the height of the peak.
    '''
    window = signal.windows.general_gaussian(winlen, p, sigma)
    window /= np.sum(window)

    return np.convolve(y, window, mode='same')
