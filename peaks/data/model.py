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

class Model(object):
    '''
    Base class for all model objects.
    '''
    def __init__(self, spec):
        self.spectrum = spec # The spectrum associated with this model
        self.params = [] # For a sum of n functions, each accepting m
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
    def __init__(self, spec):
        super(ModelGauss, self).__init__(spec)

    def Func(self, x, a, mu, sigma):
        '''
        Create a Gaussian distribution centered around mu over the domain
        given by x.
        '''
        return a * np.exp(-(x-mu)) ** 2 / (2 * sigma ** 2)


