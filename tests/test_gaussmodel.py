# Class to be tested
from peaks.data.models import ModelGauss
from peaks.data.spectrum import Spectrum
import unittest

import numpy as np
import pandas as pd

class TestModelGauss(unittest.TestCase):
    def test_known_signal(self):
        # Compute a dummy spectrum object with known peak parameters
        a = 2
        mu = 24
        sigma = 5
        x = np.linspace(0, 100, num=100)
        g = ModelGauss.gauss(x, a, mu, sigma)

        spec = Spectrum.from_arrays(x, g)

        # See if fitting proceeds at all
        mg = ModelGauss(spec, None)
        guess = mg.guess_parameters()
        self.assertNotEqual(len(guess), 0)
        self.assertEqual(mg.fit(guess), True)

        # See if fitting matches the expected signal parameters
        self.assertAlmostEqual(a, mg.params[0], places=2)
        self.assertAlmostEqual(mu, mg.params[1], places=2)
        self.assertAlmostEqual(sigma, mg.params[2], places=2)

        # See if predicting over the signal domain gets essentially the same signal
        pred = mg.evaluate_model()
        for actual, pred in zip(g, pred):
            self.assertAlmostEqual(actual, pred, delta=0.01)
    
    def test_many_signals(self):
        '''
        Generate many Gauss signals and attempt fits
        '''
        #print("\na\tmu\tsig")
        #print('-' * 20)
        # reproducibility
        np.random.seed(0)
        x = np.linspace(0, 100, num=100)
        for _ in range(10):
            a = np.random.randint(1, high=5)
            mu = np.random.randint(10, high=90)
            sig = np.random.randint(1, high=10)

            #print("{}\t{}\t{}".format(a, mu, sig))

            g = ModelGauss.gauss(x, a, mu, sig)
            spec = Spectrum.from_arrays(x, g)

            # See if fitting proceeds at all
            mg = ModelGauss(spec, None)
            guess = mg.guess_parameters(peak_range=(0, 1))
            self.assertNotEqual(len(guess), 0)
            self.assertEqual(mg.fit(guess), True)

            # See if fitting matches the expected signal parameters
            self.assertAlmostEqual(a, mg.params[0], delta=0.1)
            self.assertAlmostEqual(mu, mg.params[1], delta=0.5)
            self.assertAlmostEqual(sig, mg.params[2], delta=0.1)
    
    def test_overlapping_signal(self):
        # Construct a signal with two overlapping signals of equal height
        x = np.linspace(0, 100, num=100)
        params = [1, 45, 5, 1, 55, 5]
        g = np.zeros(len(x))
        for i in range(0, len(params), 3):
            g += ModelGauss.gauss(x, params[i], params[i+1], params[i+2])

        spec = Spectrum.from_arrays(x, g)

        # See if fitting proceeds at all
        mg = ModelGauss(spec, None)
        guess = mg.guess_parameters(peak_range=(0, 5))
        self.assertNotEqual(len(guess), 0)
        # Did we get the right number of params?
        self.assertEqual(len(guess), len(params))
        self.assertEqual(mg.fit(guess), True)

        # Are all the parameters equal?
        # sort since peak order doesn't matter
        # this isn't robust in other comparisons but for here
        # it's fine
        for model, true in zip(sorted(mg.params), sorted(params)):
            self.assertAlmostEqual(model, true, delta=0.1)

if __name__ == '__main__':
    unittest.main()