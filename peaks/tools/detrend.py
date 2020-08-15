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

def rolling_ball(y, minmax_len, smooth_len):
    '''
    Port of the rolling ball algorithm as implemented in
    Kneen and Annegarn (1996). Performs minimization, followed
    by maximization, on a sliding window given by minmax_len. The
    signal is then smoothed by applying a boxcar filter with neighborhood
    smooth_len. The effect of the process is to preserve high-frequency 
    features in the spectrum while removing gradual trendlines.

    Returns the background determined by this procedure.
    '''    
    mins = np.zeros(len(y))
    maxs = np.zeros(len(y))
    background = np.zeros(len(y))
    
    # Minimize on moving window
    for i in range(len(y)):
        window_left = max(0, i - minmax_len)
        window_right = min(i + minmax_len + 1, len(y))
        mins[i] = y[window_left:window_right].min()
    
    # Maximize on moving window
    for i in range(len(mins)):
        window_left = max(0, i - minmax_len)
        window_right = min(i + minmax_len + 1, len(mins))
        maxs[i] = mins[window_left:window_right].max()
    
    # Smooth on the other window parameter
    for i in range(len(maxs)):
        window_left = max(0, i - smooth_len)
        window_right = min(i + minmax_len + 1, len(maxs))
        background[i] = np.mean(maxs[window_left:window_right])
    
    return y - background