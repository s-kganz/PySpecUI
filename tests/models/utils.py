'''
Util functions for testing
'''

def gauss(a, mu, sigma, x):
    '''
    Generate a Gaussian signal.
    '''
    return a*np.exp(-(x-mu)**2/(2*sigma**2))