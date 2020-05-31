'''
Implements base and derived classes for model representation in the
application.

NOTE: All models are represented as a sum of an arbitrary number of
parameter-adjusted functions evaluated over the same domain (i.e.
the frequency field of a spectrum object). A valid model
defines the function and its behavior for determining 1) the
number of functions to fit, 2) making an initial guess
at the function parameters, and 3) tuning the parameters
to an optimal solution that is retained by the object.
'''

import numpy as np
from scipy import signal
from scipy.optimize import least_squares


def r_squared(a, b):
    '''
    Compute the variance in a explained by b.

    Both a and b need to be numpy arrays.
    '''
    ss_tot = np.sum(np.square(a - np.mean(a)))
    ss_resid = np.sum(np.square(a - b))
    
    return 1 - (ss_resid / ss_tot)

class Model(object):
    '''
    Base class for all model objects.
    '''

    def __init__(self, spec):
        self.spectrum = spec  # The spectrum associated with this model
        self.params = []  # For a sum of n functions, each accepting m
                          # parameters, this becomes a flat array with
                          # m * n elements

    @staticmethod
    def Func():
        '''
        The function this model uses to fit spectra.
        '''
        raise NotImplementedError("Model function must be defined!")

    def Fit(self, params):
        '''
        Do final fitting procedure, using the passed parameters as an estimate
        of the true parameters.
        '''
        raise NotImplementedError("Fitting procedure must be defined!")

    def Predict(self, domain):
        '''
        Evaluate a well-defined model over a certain domain.
        '''
        raise NotImplementedError("Model prediction must be defined!")

    def EvalModel(self, params=None):
        '''
        Evaluate the model on its own domain, optionally specifying parameters to use
        instead of those retained by a .Fit() call.
        '''
        raise NotImplementedError("Model evaluation must be defined!")

    def ParamGuess(self):
        '''
        Estimate the parameters of the true model. The output of this function should
        be inspected and then passed to .Fit() to generate the final, tuned model.
        '''
        raise NotImplementedError("Model parameter estimation must be defined!")


class ModelGauss(Model):
    '''
    Model utilizing Gaussian peaks to fit spectra.
    '''

    def __init__(self, spec, peak_range=(0, None)):
        self.peak_range = peak_range
        super(ModelGauss, self).__init__(spec)

    @staticmethod
    def Func(x, a, mu, sigma):
        '''
        Create a Gaussian distribution centered around mu over the domain
        given by x.
        '''
        return a*np.exp(-(x-mu)**2/(2*sigma**2))
    
    def EvalModel(self, params=None):
        '''
        Generate a model over the given parameters on the domain
        specified by the model's spectrum object. If no parameters
        are specified, use the object's parameters as set by a call
        to Fit().

        Params must be a 1D array with 3*n elements, where n
        is the number of Gaussian peaks specified
        '''
        if type(params) == type(None): 
            params = self.params

        x = self.spectrum.getx()

        ret = np.zeros(len(x))
        for i in range(0, len(params), 3):
            ret += ModelGauss.Func(x, params[i], params[i+1], params[i+2])
        
        return ret

    def ParamGuess(self, polyorder=2, winlen=None):
        '''
        Guess gaussian peak parameters from minima in the second derivative.
        
        Returns a flat array of approximate peak parameters
        '''
        sig, xax = self.spectrum.gety(), self.spectrum.getx()
        assert(len(sig) == len(xax))
        # Calculate savgol parameters
        delta = abs(xax[1] - xax[0])
        if not winlen: winlen = int(len(sig) / 10) # 10% of data window
        if winlen % 2 == 0: winlen += 1 # make sure the window is odd
        
        # Calculate second derivative
        d2 = signal.savgol_filter(sig, winlen, polyorder, deriv=2, delta=delta)
        
        # Find troughs in the signal by finding peaks in the negative derivative
        # Very rarely, small peaks show minima above the x-axis, so there is no
        # height constraint
        peaks, _ = signal.find_peaks(-d2)
        
        # Get the widths as well for calculating sigma
        widths = signal.peak_widths(-d2, peaks)
        
        # Wrap up all candidate peaks together, determine the best ones by how much
        # they improve model fit
        candidates = list(zip(sig[peaks], peaks, widths[0] / 2))
        # sort by peak size
        candidates.sort(key=lambda x: x[0], reverse=True)

        accepted = []
        
        min_peaks, max_peaks = self.peak_range[0], self.peak_range[1]
        for i in range(len(candidates)):
            # Keep peaks whose parameters are reasonable
            # nothing 0 or less
            if any(c < 0 or np.isclose(c, 0) for c in candidates[i]): continue
            # mu must be within the bounds of the frequency domain
            if not min(xax) <= candidates[i][1] < max(xax): continue
            
            # Accept the new peak
            accepted.extend(candidates[i])

            # Stop if max peaks reached
            if len(accepted) == max_peaks:
                break
        
        # Raise a warning if minimum number of peaks was not reached
        if len(accepted) < min_peaks:
            print("Only found {} peaks (minimum was {})".format(len(accepted), min_peaks))
        
        return accepted

    def Fit(self, params):
        '''
        Tune passed set of parameters with an optimizer. Returns a Boolean
        indicating whether fitting was successful
        '''
        true_signal = self.spectrum.gety()
        fit_result = least_squares(
            lambda p: self.EvalModel(p) - true_signal,
            params,
            bounds = (0, np.inf), # nothing should be below 0
            method='trf')
        
        self.params = fit_result['x']
        return True

    def Predict(self, x):
        '''
        Extract a section of or extrapolate this model to a custom domain.
        '''
        if not self.params:
            raise RuntimeError("The model's parameters must be set by a\
                                .Fit() call before doing a prediction.")
        ret = np.zeros(len(x))

        for i in range(0, len(self.params), 3):
            ret += ModelGauss.Func(x, params[i], params[i+1], params[i+2])

        return ret        
        

        

