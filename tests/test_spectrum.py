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

if __name__ == '__main__':
    unittest.main()