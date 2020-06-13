import unittest
from peaks.data.ds import DataSource

import numpy as np
import pandas as pd

class TestDataSource(unittest.TestCase):
    def test_load_csv(self):
        # write some data to a csv
        x = np.linspace(1, 10, num=50)
        y = np.sin(x)

        df = pd.DataFrame(
            {
                'freq': x,
                'spec': y
            }
        )

        df.to_csv('tempdata.csv')

        ds = DataSource()
        t_id = ds.AddTraceFromCSV('tempdata.csv', )

        # Get the trace object
        trace = ds.GetTraceByID(t_id)

        self.assertEqual(len(trace.getx()), df.shape[0])


if __name__ == '__main__':
    unittest.main()
