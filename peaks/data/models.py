'''
Implements base and derived classes for model representation in the
application.

NOTE: All models are represented as a sum of an arbitrary number of
parameter-adjusted functions evaluated over the same domain (i.e.
the frequency field of a spectrum object). A valid model
defines the function and its behavior for determining 1) the
number of functions to fit, 2) making an initial guess
at the function parameters, and 3) tuning the parameters
to an optimal solution that is returned to the user.
'''

import numpy as np
from scipy import signal


class Model(object):
    '''
    Base class for all model objects.
    '''

    def __init__(self, spec):
        self.spectrum = spec  # The spectrum associated with this model
        self.params = []  # For a sum of n functions, each accepting m
                        # parameters, this becomes a matrix with
                       # n rows and m columns.
        self.nfuncs = 0

    def Func(self, x, *args):
        '''
        The function this model uses to fit spectra.
        '''
        raise NotImplementedError("Model function must be defined!")

    def ParamGuess(self):
        '''
        Make an initial attempt at finding model parameters.
        '''
        raise NotImplementedError("Parameter guess function must be defined!")

    def ParamTune(self):
        '''
        Tune parameter guesses to an optimal/convergent value.
        '''
        raise NotImplementedError("Paremter tuning must be defined!")

    def Predict(self, domain):
        '''
        Evaluate a well-defined model over a certain domain.
        '''
        raise NotImplementedError("Model prediction must be defined!")


class ModelGauss(Model):
    '''
    Model utilizing Gaussian peaks to fit spectra.
    '''

    def __init__(self, spec, peak_counts=()):
        super(ModelGauss, self).__init__(spec)

    def Func(self, x, a, mu, sigma):
        '''
        Create a Gaussian distribution centered around mu over the domain
        given by x.
        '''
        return a * np.exp(-(x-mu)) ** 2 / (2 * sigma ** 2)

    def ParamGuess(self, window_length=51, polyorder=2):
        '''
        Guess paramters for an undefined number of Gaussian curves in sig
        based off of zero crossings in the second derivative.
        '''
        sig, xax = self.spectrum.getx(), self.spectrum.gety()
        if len(sig) != len(xax):
            raise ValueError(
                "Signal and frequency axes are of different length (ModelGauss.ParamGuess)")
        elif len(sig) < 1:
            raise ValueError(
                "Signal must have at least 2 cells (ModelGauss.ParamGuess)")

        deltax = abs(xax[1] - xax[0])
        d2 = signal.savgol_filter(sig,
                                  window_length=window_length,
                                  polyorder=polyorder,
                                  deriv=2, delta= deltax)

        zero_crossings = np.where(np.diff(np.signbit(d2)))[0]
        # Consider the indices of ZCs, not the frequency domain itself
        zc_ind = zero_crossings.index
        # Each element is a list of [left_bound, right_bound]
        pairs = []
        # If the first zc is negative to positive, peak area recorded will
        # be positive. We want the peak area below x axis.
        neg_to_pos = int(d2[zc_ind[0]+1] > d2[zc_ind[0]-1])
        for i in range(neg_to_pos, len(zc_ind), 2):
            left, right = zc_ind[i], zc_ind[i+1]
            pairs.append([left, right])

        # Sort by peak area
        pairs.sort(key=lambda x: sum(d2[x[0]:x[1]])), reverse=True)

        return param_guess
