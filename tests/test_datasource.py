'''
Test internal data manager.
'''

import unittest
import time
import random
from concurrent.futures import ThreadPoolExecutor
from peaks.data.datasource import DataSource
from peaks.data.spectrum import Spectrum
from peaks.data.models import Model

from kivy.tests.common import GraphicUnitTest

def dummyfunc(ret, ds):
    '''
    Simple function that returns data at different times.
    '''
    time.sleep(random.random() * 1)
    ds._post_data(ret)

ds = DataSource()

class TestDataSource(GraphicUnitTest):
    def test_manythreads(self):
        '''
        Test that data incoming from multiple threads is ingested properly.
        '''
        ds = DataSource()
        executor = ThreadPoolExecutor(max_workers=10)
        rets = []

        futures = [executor.submit(dummyfunc, i, ds) for i in range(10)]
        while not (all(f.done() for f in futures) and ds.is_queue_empty()):
            ret = ds.get_next_task()
            if ret is not None: rets.append(ret)
        
        # Assert that all values made it through
        self.assertEqual(set(range(10)), set(rets))
        # Assert that data was ingested in the proper way
        self.assertEqual(len(ds.traces), 0)
    
    def test_sorting(self):
        '''
        Test that models and spectra are ingested correctly.
        '''
        x, y = [0, 1], [2, 3]
        s = Spectrum.from_arrays(x, y)
        ds = DataSource()
        for i in range(3):
            ds._post_data(Spectrum.from_arrays(x, y))
            ds._post_data(Model(s))
        
        while not ds.is_queue_empty():
            ds.get_next_task()

        models = ds.get_all_models()
        specs = ds.get_all_spectra()

        # Check that the correct number of each was ingested
        self.assertEqual(len(models), 3)
        self.assertEqual(len(specs), 3)

        # Check that everything in the dicts is the right value
        self.assertTrue(all(isinstance(m, Model) for m in models.values()))
        self.assertTrue(all(isinstance(s, Spectrum) for s in specs.values()))

        # Check that each object has a unique id and that querying the source
        # by the idea returns something
        ids = list(models.keys()) + list(specs.keys())
        self.assertEqual(len(ids), len(set(ids)))

        for this_id in ids:
            self.assertIsNotNone(ds.get_trace(this_id))
        
        # Check that querying a nonexistant trace raises an error
        with self.assertRaises(ValueError):
            ds.get_trace(-9999)

        
if __name__ == '__main__':
    unittest.main()

