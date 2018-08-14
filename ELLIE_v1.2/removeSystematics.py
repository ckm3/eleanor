import numpy as np
import matplotlib.pyplot as plt
from astropy.io import fits
import sys, os, math
from gaiaTIC import ticSearchByContam as tsbc
from pixelCorrection import sortByDate
from scipy.optimize import minimize
from photutils import CircularAperture, aperture_photometry
from lightkurve import KeplerTargetPixelFile as ktpf
from lightkurve import SFFCorrector


###################
# Loads  all data #
#     ADDED       #  
################### 
def load_data(id, camera, chip):
    file = './figures/{}_tpf.fits'.format(id)
    theta, delx, dely = np.loadtxt('pointingModel_{}-{}.txt'.format(camera, chip), skiprows=1,
                                   usecols=(1,2,3), unpack=True)
    tpf  = ktpf.from_fits(file)
    hdu = fits.open(file)

    cen_x, cen_y = len(tpf.flux[0])/2., len(tpf.flux[0])/2.

    # Creates estimated center location taking the pointing model into account            
    x_point = cen_x * np.cos(np.radians(theta)) - cen_y * np.sin(np.radians(theta)) - delx
    y_point = cen_x * np.sin(np.radians(theta)) + cen_y * np.cos(np.radians(theta)) - dely

    return x_point, y_point
    

###################
# Minimize Jitter #
#     ADDED       #
###################
def parabola(params, x, y, f_obs, y_err):
    c1, c2, c3, c4, c5 = params
    f_corr = f_obs * (c1 + c2*(x-2.5) + c3*(x-2.5)**2 + c4*(y-2.5) + c5*(y-2.5)**2)
    return np.sum( ( (1-f_corr)/y_err)**2)


###################
# Corrects Jitter #
#     ADDED       #  
###################
def jitter_correction(lc, x_point, y_point): #id, camera, chip, lc):
#    lc, x_point, y_point = load_data(camera, chip)
#    x_point, y_point = load_data(id, camera, chip)

    # Masks out anything >= 3 sigma above the mean
    mask = np.ones(len(lc), dtype=bool)
    for i in range(5):
        lc_new = []
        std_mask = np.std(lc[mask])

        inds = np.where(lc <= np.mean(lc)-2.5*std_mask)

        y_err = np.ones(len(lc))*np.std(lc)

        for j in inds:
            y_err[j] = np.inf
            mask[j]  = False

        if i == 0:
            initGuess = [3, 3, 3, 3, 3]
        else:
            initGuess = test.x

        bnds = ((-15.,15.), (-15.,15.), (-15.,15.), (-15.,15.), (-15.,15.))
        test = minimize(parabola, initGuess, args=(x_point, y_point, lc, y_err), bounds=bnds)

        c1, c2, c3, c4, c5 = test.x
        lc_new = lc * (c1 + c2*(x_point-2.5) + c3*(x_point-2.5)**2 + c4*(y_point-2.5) + c5*(y_point-2.5)**2)

    return lc_new
 
###################
# Corrects  Roll  #
###################
def roll_correction(lc, x_point, y_point):
#    lc, x_point, y_point = load_data(camera, chip)
    time = np.arange(0,len(lc),1)

    sff = SFFCorrector()
    lc_corrected = sff.correct(time, lc, x_point, y_point, niters=1,
                               windows=1, polyorder=5)

    return lc_corrected.flux
#    long_term_trend = sff.trend

#    plt.plot(time, lc, 'ko', ms=4)
#    plt.plot(time, lc, 'o', color='#3498db', ms=3)
#    plt.plot(time, lc_corrected.flux*long_term_trend, 'o', color='pink', ms=3)
#    plt.show()
#    plt.close()
