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
# GENERAL MODULES
import numpy as np
from scipy import signal
from scipy.optimize import least_squares
from pubsub import pub
import asyncio

# WX MODULES
from wx import GetApp

# NAMESPACE MODULES
from peaks.data.data_helpers import Trace

__all__ = ['ModelGauss']

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

        self.params = None  # For a sum of n functions, each accepting m
                            # parameters, this becomes a flat array with
                            # m * n elements

        self.trace = None # The prediction this model makes on the frequency domain
                          # of the spectrum.

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
    
    def GetTunerParameters(self):
        '''
        After self.paramters has been set, return a dictionary with meaningful labels
        so that a tuner window can create a meaningful interface for tweaking the model.
        '''
        raise NotImplementedError("")

    def SetTunerParameters(self):
        '''
        Facilitate communication with tuner windows by accepting a rolled-up dictionary
        of model parameters, setting the object's internal parameters, and recalculating
        the trace.
        '''


class ModelGauss(Model, Trace):
    '''
    Model utilizing Gaussian peaks to fit spectra.
    '''

    def __init__(self, spec, id):
        # Call the parents directly to ensure that they
        # actually get called
        Model.__init__(self, spec)
        Trace.__init__(self)
        self.model_name = "Gaussian"
        self.id = id

    @staticmethod
    def Gauss(x, a, mu, sigma):
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
        if params is None:
            params = self.params

        x = self.spectrum.getx()

        ret = np.zeros(len(x))
        for i in range(0, len(params), 3):
            ret += self.Gauss(x, params[i], params[i+1], params[i+2])

        return ret

    def ParamGuess(self, polyorder=2, winlen=None, peak_range=(0, None)):
        '''
        Guess gaussian peak parameters from minima in the second derivative.

        Returns a flat array of approximate peak parameters.
        '''
        sig, xax = self.spectrum.gety(), self.spectrum.getx()
        try:
            assert(len(sig) == len(xax))
        except AssertionError as e:
            pub.sendMessage(
                'Logging.Error', 
                caller='ModelGauss.ParamGuess', 
                msg="Signal and frequency axes are not the same length."
            )
            return
        
        # Calculate savgol parameters
        delta = abs(xax[1] - xax[0])
        if not winlen:
            winlen = int(len(sig) / 10)  # 10% of data window
        if winlen % 2 == 0:
            winlen += 1  # make sure the window is odd

        # Calculate second derivative
        d2 = signal.savgol_filter(sig, winlen, polyorder, deriv=2, delta=delta)

        # Find troughs in the signal by finding peaks in the negative derivative
        # Very rarely, small peaks show minima above the x-axis, so there is no
        # height constraint
        peaks, _ = signal.find_peaks(-d2)

        # Get the widths as well for calculating sigma
        widths = signal.peak_widths(-d2, peaks)
        min_peaks, max_peaks = peak_range[0], peak_range[1]
        # Wrap up all candidate peaks together, determine the best ones by how much
        # they improve model fit
        candidates = list(zip(sig[peaks], peaks, widths[0] / 2))
        # sort by peak size, then width, cut off extra peaks
        candidates.sort(key=lambda x: (x[2], x[0]), reverse=True)
        accepted = []

        for i in range(len(candidates)):
            # Stop if max peaks reached
            if len(accepted) // 3 == max_peaks:
                break
            
            # Keep peaks whose parameters are reasonable
            # nothing 0 or less
            if any(c < 0 or np.isclose(c, 0) for c in candidates[i]):
                continue
            # mu must be within the bounds of the frequency domain
            if not min(xax) <= candidates[i][1] < max(xax):
                continue

            # Accept the new peak
            accepted.extend(candidates[i])

        # Raise an error if minimum number of peaks was not reached
        if len(accepted) // 3 < min_peaks:
            pub.sendMessage(
                'Logging.Error', 
                caller='ModelGauss.ParamGuess', 
                msg="Minimum number of peaks not reached ({} vs. min of {})".format(len(accepted), min_peaks)
            )
        # Raise an error if no peaks were found
        if len(accepted) == 0:
            pub.sendMessage(
                'Logging.Error',
                caller='ModelGauss.ParamGuess',
                msg='No peaks found.'
            )

        return accepted

    def Fit(self, params):
        '''
        Tune passed set of parameters with an optimizer. Returns a Boolean
        indicating whether fitting was successful.
        '''
        true_signal = self.spectrum.gety()
        fit_result = least_squares(
            lambda p: self.EvalModel(p) - true_signal,
            params,
            bounds=(0, np.inf),  # nothing should be below 0
            method='trf')

        self.params = fit_result['x']
        self.trace = self.EvalModel()
        return True

    def Predict(self, x):
        '''
        Extract a section of or extrapolate this model to a custom domain.
        '''
        if not self.params:
            pub.sendMessage(
                'Logging.Error',
                caller='ModelGauss.Predict',
                msg="The model's parameters must be set by a .Fit() call before doing a prediction."
            )
            return
        ret = np.zeros(len(x))

        for i in range(0, len(self.params), 3):
            ret += self.Gauss(x, params[i], params[i+1], params[i+2])

        return ret
    
    # Implementation of trace interface
    def getx(self):
        '''
        Return the domain of the underlying spectrum object.
        '''
        return self.spectrum.getx()

    def gety(self):
        '''
        Return the prediction this model makes on the domain
        of the spectrum object. This is kept in memory since this function
        may be called many times by plotting functions.
        '''
        if self.trace is None:
            pub.sendMessage(
                'Logging.Error',
                caller='ModelGauss.gety',
                msg="Model has not been fully fitted, cannot plot."
            )
            return

        return self.trace

    def label(self):
        '''
        Legend label for when the model is plotted.
        '''
        return "{} ({})".format(self.spectrum.name, self.model_name)
    
    # Tuner communication functions
    def GetTunerParameters(self):
        '''
        Roll up current model parameters into a labeled dictionary for display
        in a tuner window.
        '''
        if self.params is None:
            raise RuntimeError("Model that has not been fitted cannot be tuned.")
            
        ret = []
        for i in range(0, len(self.params), 3):
            ret.append(
                {
                    'a': ('float', self.params[i]),
                    'mu': ('float', self.params[i+1]),
                    'sigma': ('float', self.params[i+2])
                }
            )
        
        # sort by mu so that peak n corresponds to peak n to the viewer
        return sorted(ret, key=lambda x: x['mu'])

    def SetTunerParameters(self, newparams):
        '''
        Receive a set of model parameters from a tuner and set the model object's
        properties and trace.
        '''
        if not len(newparams) % 3 == 0:
            raise ValueError('Length of new parameters must be divisible by 3.')
        
        # Re-evaluate the trace
        self.params = newparams.copy() # everything should be a float so deepcopy isn't necessary
        self.trace = self.EvalModel()

    def __str__(self):
        return self.label()

def ExecModel(M, spec, params={}):
    def run(M, spec, params):
        m = M(spec, None) # pass a blank id for now, let the data manager set it
        pub.sendMessage('UI.SetStatus', text='Fitting model {}...'.format(m.model_name))

        if not m.Fit(m.ParamGuess(**params)):
            return

        pub.sendMessage(
            'Data.AddModel',
            model=m
        )
        pub.sendMessage('UI.SetStatus', text='Done.')
    
    pub.sendMessage('StartToolThread', lambda: run(M, spec, params))

pub.subscribe(ExecModel, 'Data.Model.Create')
