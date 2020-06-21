import unittest
from peaks.data.ds import DataSource

import numpy as np
import pandas as pd
import os

class TestDataSource(unittest.TestCase):
    def test_load_csv(self):
        '''
        Test basic reading from a csv
        '''
        # write some data to a csv
        x = np.linspace(1, 10, num=50)
        y = np.sin(x)

        df = pd.DataFrame(
            {
                'freq': x,
                'spec': y
            }
        )

        df.to_csv('tempdata.csv', index=False)

        ds = DataSource()
        t_id = ds.AddTraceFromCSV(
            'tempdata.csv',
            options = {
                'freqColInd': df.columns.get_loc('freq'),
                'specColInd': df.columns.get_loc('spec')
        })
        self.assertIsNotNone(t_id)
        # Get the trace object
        trace = ds.GetTraceByID(t_id)

        for i in range(len(x)):
            # Values change a tiny bit between IO operations, so check to only
            # a couple places
            self.assertAlmostEqual(x[i], trace.getx()[i], places=5)
            self.assertAlmostEqual(y[i], trace.gety()[i], places=5)

        # Cleanup
        os.remove('tempdata.csv')
    
    def test_col_selection(self):
        '''
        Test reading several traces from one file.
        '''
        col_count = 4
        # make some data where each column has different values
        data = []
        for rownum in range(10):
            row = [rownum]
            row.extend(list(range(1,col_count+1)))
            data.append(row)

        # make the dataframe
        df = pd.DataFrame(data, columns=list('abcde'))

        # write to csv
        df.to_csv('tempdata.csv', index=False)

        ds = DataSource()
        for colnum in range(1,col_count+1):
            t_id = ds.AddTraceFromCSV(
                'tempdata.csv',
                options = {
                    'freqColInd': df.columns.get_loc('a'),
                    'specColInd': colnum
            })
            self.assertIsNotNone(t_id)
            # Get the trace object
            trace = ds.GetTraceByID(t_id)
            self.assertEqual(trace.gety()[0], colnum)
        
        # cleanup
        os.remove('tempdata.csv')

    def test_multiple_traces(self):
        '''
        Test whether traces are deleted from the manager properly
        '''
        read_count = 3
        # quick dataframe to pass in
        x = np.linspace(0, 10)
        df = pd.DataFrame({
            'freq': x,
            'spec': np.sin(x)
        })

        # write to a temp location
        df.to_csv('tempdata.csv', index=False)

        # call the read function multiple times
        ds = DataSource()
        for _ in range(read_count):
            t_id = ds.AddTraceFromCSV(
                'tempdata.csv',
                options = {
                    'freqColInd': 0,
                    'specColInd': 1
            })
            self.assertIsNotNone(t_id)

        # assert that the read happened
        self.assertEqual(len(ds.traces), read_count)

        # assert that there's no aliasing
        ds.traces[0].getx()[5] = 99999
        for i in range(1, read_count):
            self.assertNotEqual(ds.traces[i].getx()[5], 99999)

        # assert that all traces got unique ids
        id_set = set(t.id for t in ds.traces)
        id_lis = [t.id for t in ds.traces]
        self.assertEqual(len(id_set), len(id_lis))

        # test getter function
        for i in range(len(ds.traces)):
            self.assertEqual(ds.GetTraceByID(ds.traces[i].id).id, ds.traces[i].id)
        
        self.assertRaises(ValueError, ds.GetTraceByID, 99999)

        # remove a trace
        ds.DeleteTrace(id_lis[0])
        self.assertEqual(len(id_lis)-1, len(ds.traces))
        for id in [t.id for t in ds.traces]:
            self.assertNotEqual(id, id_lis[0])
        
        # cleanup
        os.remove('tempdata.csv')

if __name__ == '__main__':
    unittest.main()
