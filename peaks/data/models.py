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
# KIVY MODULES
from kivy_garden.graph import MeshLinePlot

# GENERAL MODULES
import numpy as np
from scipy import signal
from scipy.optimize import least_squares
from pubsub import pub
import asyncio
from random import random

# NAMESPACE MODULES
from peaks.data.data_helpers import Trace

__all__ = ['Model', 'ModelGauss']

def r_squared(a, b):
    '''
    Compute the variance in a explained by b.

    Both a and b need to be numpy arrays.
    '''
    ss_tot = np.sum(np.square(a - np.mean(a)))
    ss_resid = np.sum(np.square(a - b))

    return 1 - (ss_resid / ss_tot)

def gauss(x, a, mu, sigma):
    '''
    Create a Gaussian distribution centered around mu over the domain
    given by x.
    '''
    return a*np.exp(-(x-mu)**2/(2*sigma**2))

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
        
        # Representation of the model in the graph
        self.mesh = MeshLinePlot(color=[random(), random(), random(), 1])
        self._bounds = None

    def fit(self, params):
        '''
        Do final fitting procedure, using the passed parameters as an estimate
        of the true parameters.
        '''
        raise NotImplementedError("Fitting procedure must be defined!")

    def predict(self, domain):
        '''
        Evaluate a well-defined model over a certain domain.
        '''
        raise NotImplementedError("Model prediction must be defined!")

    def evaluate_parameters(self, params=None):
        '''
        Evaluate the model on its own domain, optionally specifying parameters to use
        instead of those retained by a .Fit() call.
        '''
        raise NotImplementedError("Model evaluation must be defined!")

    def guess_parameters(self):
        '''
        Estimate the parameters of the true model. The output of this function should
        be inspected and then passed to .Fit() to generate the final, tuned model.
        '''
        raise NotImplementedError("Model parameter estimation must be defined!")
    
    def get_tuner_parameters(self):
        '''
        After self.paramters has been set, return a dictionary with meaningful labels
        so that a tuner window can create a meaningful interface for tweaking the model.
        '''
        raise NotImplementedError("")

    def set_tuner_parameters(self):
        '''
        Facilitate communication with tuner windows by accepting a rolled-up dictionary
        of model parameters, setting the object's internal parameters, and recalculating
        the trace.
        '''


class ModelGauss(Model, Trace):
    '''
    Model utilizing Gaussian peaks to fit spectra.
    '''

    def __init__(self, spec, id, name='Gaussian'):
        # Call the parents directly to ensure that they
        # actually get called
        Model.__init__(self, spec)
        Trace.__init__(self)
        self.model_name = name
        self.id = id

    def evaluate_parameters(self, params):
        '''
        Return the result of evaluating the passed model parameters over the x-axis
        specified by this object.
        '''
        x = self.spectrum.getx()
        ret = np.zeros(len(x))

        ret = np.zeros(len(x))
        for i in range(0, len(params), 3):
            ret += gauss(x, params[i], params[i+1], params[i+2])
        
        return ret

    def update_model(self, params):
        '''
        Update the internal representation of this object using the passed
        parameters.
        '''
        self.params = params
        self.trace = self.evaluate_parameters(params)
        self._update_bounds()
        self._update_mesh()

    def guess_parameters(self, poly_order=2, winlen=None, peak_min=0, peak_max=None, **kwargs):
        '''
        Guess gaussian peak parameters from minima in the second derivative.

        Returns a flat array of approximate peak parameters.
        '''
        peak_range = peak_min, peak_max
        sig, xax = self.spectrum.gety(), self.spectrum.getx()
        try:
            assert(len(sig) == len(xax))
        except AssertionError as e:
            raise ValueError('Spectral and frequency axes are not hte same length.')
        
        # Calculate savgol parameters
        delta = abs(xax[1] - xax[0])
        if not winlen:
            winlen = int(len(sig) / 10)  # 10% of data window
        if winlen % 2 == 0:
            winlen += 1  # make sure the window is odd

        # Calculate second derivative
        d2 = signal.savgol_filter(sig, winlen, poly_order, deriv=2, delta=delta)

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
            raise RuntimeError('Minimum number of peaks not reached: {}'.format(min_peaks, len(accepted) // 3))
        # Raise an error if no peaks were found
        if len(accepted) == 0:
            raise RuntimeError('No peaks found.')

        return accepted

    def fit(self, params):
        '''
        Tune passed set of parameters with an optimizer. Returns a Boolean
        indicating whether fitting was successful.
        '''
        true_signal = self.spectrum.gety()
        fit_result = least_squares(
            lambda p: self.evaluate_parameters(p) - true_signal,
            params,
            bounds=(0, np.inf),  # nothing should be below 0
            method='trf')

        # Update internal model representation
        self.update_model(fit_result['x'])
        return True

    def predict(self, x):
        '''
        Extract a section of or extrapolate this model to a custom domain.
        '''
        if not self.params:
            return
        ret = np.zeros(len(x))

        for i in range(0, len(self.params), 3):
            ret += self.gauss(x, params[i], params[i+1], params[i+2])

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
            return

        return self.trace

    def _update_mesh(self):
        self.mesh.points = zip(self.getx(), self.gety())

    def get_mesh(self):
        return self.mesh

    def _update_bounds(self):
        self._bounds = min(self.getx()), max(self.getx()), min(self.gety()), max(self.gety())

    def bounds(self):
        return self._bounds
    
    # Tuner communication functions
    def get_schema(self):
        '''
        Roll up current model parameters into a labeled dictionary for display
        in a tuner window.
        '''
        if self.params is None:
            raise RuntimeError("Model that has not been fitted cannot be tuned.")
            
        ret = dict()
        for i in range(0, len(self.params), 3):
            ret["Peak {}".format(i // 3 + 1)] = {
                    'Height': {
                        'type': 'float',
                        'min': 0,
                        'max': max(self.spectrum.gety()),
                        'value': self.params[i]
                    },
                    'Center': {
                        'type': 'float',
                        'min': 0,
                        'max': max(self.spectrum.getx()),
                        'value': self.params[i+1]
                    },
                    'Width': {
                        'type': 'float',
                        'min': 0,
                        'max': max(self.spectrum.getx()),
                        'value': self.params[i+2]
                    }
                }
        
        return ret

    def push_schema(self, schema):
        '''
        Receive a set of model parameters from a tuner and set the model object's
        properties and trace.
        '''
        newparams = list()
        for key in schema:
            for param in schema[key]:
                newparams.append(schema[key][param])
        if not len(newparams) % 3 == 0:
            raise ValueError('Length of new parameters must be divisible by 3.')
        
        # Re-evaluate the trace
        self.params = newparams.copy() # everything should be a float so deepcopy isn't necessary
        self.trace = self.update_model(newparams)

    def __str__(self):
        return self.model_name