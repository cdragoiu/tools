import numpy as np

class RansacPoly:
    '''
    Method to fit a k-th order polynomial function to a set of 2D noisy data points.
    Steps:
        - randomly select minimum number of data points to fit the given model
        - determine how many data points match the fitted model (based on a maximum distance)
        - if enough points match the fitted model refit the model using all matching data points
            - store best fit based on number of matched data points
        - redo all steps N times to find best fit
    '''

    def __init__(self, nr_tries, max_dif, min_percent):
        '''
        Args:
            nr_tries:    number of tries to find the best fit
            max_dif:     maximum difference between data points and fitted model to define inlieres
            min_percent: minimum percentage of data points that are considered inlieres
        '''

        self.nr_tries = nr_tries
        self.max_dif = max_dif
        self.min_percent = min_percent

        self.__x = None  # numpy array of data point x-values
        self.__y = None  # numpy array of data point y-values
        self.__fit_params = None  # parameters of polynomial fit
        self.__sel_idx = None  # indices of selected data points (inliers)

    def set_2d_data(self, x, y):
        '''
        Args:
            x: list or numpy array of data point x-values
            y: list of numpy array of data point y-values
        '''

        # check x for valid type
        if isinstance(x, (list, np.ndarray)):
            tmp = np.array(x)
            if tmp.dtype in [int, float]:
                self.__x = tmp
            else:
                print('invalid data type: x elements must be int or float')
        else:
            print('invalid data type: x must be a list or a numpy array')

        # check y for valid type
        if isinstance(y, (list, np.ndarray)):
            tmp = np.array(y)
            if tmp.dtype in [int, float]:
                self.__y = tmp
            else:
                print('invalid data type: y elements must be int or float')
        else:
            print('invalid data type: y must be a list or a numpy array')

    def fit(self, poly_ord):
        ''' Fit provided data points with a polynomial function of order 'poly_ord'. '''

        if self.__x is None or self.__y is None:
            print('please first provide the data points by calling "set_2d_data()"')
            return

        self.__sel_idx = None
        for i in range(self.nr_tries):
            # get 'poly_ord + 1' random data points
            rnd_idx = np.random.randint(self.__x.size, size=poly_ord+1)

            try:
                # fit model to selected data points
                fit_params = np.polynomial.polynomial.polyfit(self.__x[rnd_idx],
                                                              self.__y[rnd_idx],
                                                              poly_ord)
                if fit_params is None or fit_params.size < poly_ord + 1:
                    continue

                # check all data points against fitted model
                val = np.polynomial.polynomial.polyval(self.__x, fit_params)
                sel_idx = abs(val - self.__y) < self.max_dif  # selected data points

                # store the selected data points that provide the best fit
                count = np.count_nonzero(sel_idx)
                count_best = np.count_nonzero(self.__sel_idx)
                test_size = count > self.min_percent * self.__x.size
                test_best = (self.__sel_idx is None) or (count > count_best)
                if test_size and test_best:
                    self.__sel_idx = sel_idx
            except:
                continue

        # get best fit
        if self.__sel_idx is not None:
            self.__fit_params = np.polynomial.polynomial.polyfit(self.__x[self.__sel_idx],
                                                                 self.__y[self.__sel_idx],
                                                                 poly_ord)
        else:
            self.__fit_params = None
            print('unable to fit provided data points with current parameters')

    def get_fit_params(self):
        ''' Return fit parameters. '''
        return self.__fit_params

    def get_inliers(self):
        ''' Return indices of selected data points (inliers). '''
        return self.__sel_idx
