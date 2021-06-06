#! /usr/local/bin/python3

from datafit.ransacpoly import RansacPoly
import matplotlib.pyplot as plt
import numpy as np

def test_ransacpoly(x_min, x_max, N):
    '''
    Test the RANSAC method on a set of generated data points and plot the results.
    Args:
        x_min: lower limit for x
        x_max: upper limit for x
        N:     number of points between x_min and x_max
    '''

    # generate points with random noise
    x = np.linspace(x_min, x_max, N)  # generate N points between x_min and x_max
    y = x + np.random.normal(0, 1, N) + np.random.normal(0, 5, N) * (np.random.rand(N) > 0.5)

    # ransac poly fit
    ransac_poly = RansacPoly(nr_tries=100, max_dif=3, min_percent=0.7)
    ransac_poly.set_2d_data(x, y)
    ransac_poly.fit(poly_ord=1)

    # skip if fit unsuccesful
    fit_params = ransac_poly.get_fit_params()
    if fit_params is None:
        print('nothing to display; no best fit available')
        return

    # generate fit points
    fit_x = np.linspace(x.min(), x.max(), N)
    fit_y = np.polynomial.polynomial.polyval(fit_x, fit_params)

    # display results
    sel_idx = ransac_poly.get_inliers()
    not_sel_idx = np.logical_not(sel_idx)
    plt.xlabel('x value')
    plt.ylabel('y value')
    plt.scatter(x[not_sel_idx], y[not_sel_idx],
                color='red', marker='o', label='outliers')
    plt.scatter(x[sel_idx], y[sel_idx],
                color='blue', marker='o', label='inliers')
    plt.plot(fit_x, fit_y, color='black', label='poly fit')
    plt.legend(frameon=False)
    plt.show()

if __name__ == '__main__':
    test_ransacpoly(x_min=1, x_max=50, N=100)
