'''
Test spectrum representation class.
'''
from peaks.data.spectrum import Spectrum
from kivy.tests.common import GraphicUnitTest

import pandas as pd
import unittest
import numpy as np

class TestSpectrum(GraphicUnitTest):
    def test_from_dataframe(self):
        df = pd.DataFrame(
            np.transpose(
                [[1, 2, 3, 4],
                 [1] * 4,
                 [2] * 4,
                 [3] * 4,
                 [4] * 4]
            )
        )
        for i in range(1, 5):
            s = Spectrum.from_data_frame(df, freqcol=0, speccol=i)
            self.assertTrue(s.gety()[0] == i)
            self.assertEqual(s.getx().to_list(), [1, 2, 3, 4])
    
    def test_from_arrays(self):
        arr1 = [1, 2, 3, 4]
        arr2 = [2, 4, 5, 7]
        s = Spectrum.from_arrays(arr1, arr2)
        self.assertTrue(s.getx().to_list() == arr1)
        self.assertTrue(s.gety().to_list() == arr2)
    
    def test_history(self):
        # Make some dummy functions
        def add_constant(y, const, negative=False):
            return y + const * (-1 if negative else 1)
        
        def shift_x(x, const):
            return x + const
        
        def scale_axes(x, y, factor):
            return x * factor, y * factor
        
        def rename(spec, new):
            spec.name = new
            return spec
    
        s = Spectrum.from_arrays(
            [1, 2, 3], [4, 5, 6], 
            specunit='x', frequnit='y', 
            name='testspec')
        
        s2 = s.apply_spec(add_constant, 1, negative=False)\
              .apply_freq(shift_x, 1)\
              .apply_spec_freq(scale_axes, 2)\
              .apply_object(rename, 'modified_testspec')
        
        self.assertTrue(len(s2.history) == 4)
        self.assertListEqual(s2.getx().tolist(), [4, 6, 8])
        self.assertListEqual(s2.gety().tolist(), [10, 12, 14])
        self.assertEqual(s2.name, 'modified_testspec')
        self.assertTrue(s2.specunit == 'x' and s2.frequnit == 'y')

        # Check that applying the history to another spectrum does the same operations
        s3 = Spectrum.from_arrays([2, 4, 6], [5, 6, 7], name='testspec2').apply_history(s2)
        self.assertEqual(len(s3.history), 4)
        self.assertListEqual(s3.gety().tolist(), [12, 14, 16])
        self.assertListEqual(s3.getx().tolist(), [6, 10, 14])
        self.assertEqual(s3.name, 'modified_testspec')
        


if __name__ == '__main__':
    unittest.main()