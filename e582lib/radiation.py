"""
Functions to compute thermal radiation relations for the Planck function

"""
import numpy as np
import pytest
from scipy.constants import c, h, k
#
# combine fundamental constants into two coefficients
#
# c=2.99792458e+08  #m/s -- speed of light in vacuum
# h=6.62606876e-34  #J s  -- Planck's constant
# k=1.3806503e-23  # J/K  -- Boltzman's constant

c1 = 2. * h * c**2.
c2 = h * c / k
sigma = 2. * np.pi**5. * k**4. / (15 * h**3. * c**2.)
print(sigma)


def Flambda(wavel, Temp):
    """
    Calculate the blackbody radiant exitence: pi*Blambda

    Parameters
    ----------

      wavel: float or array
           wavelength (meters)

      Temp: float
           temperature (K)

    Returns
    -------

    Flambda:  float or arr
           monochromatic radiant exitence (W/m^2/m)
    """
    Flambda_val = c1 * np.pi / (wavel**5. * (np.exp(c2 / (wavel * Temp)) - 1))
    return Flambda_val


def Blambda(wavel, Temp):
    """
    Calculate the blackbody radiance (Petty 6.1)

    Parameters
    ----------

      wavel: float or array
           wavelength (meters)

      Temp: float
           temperature (K)

    Returns
    -------

    Blambda_rad:  float or arr
           monochromatic radiant exitence (W/m^2/m/sr)
    """
    Blambda_val = c1 / (wavel**5. * (np.exp(c2 / (wavel * Temp)) - 1))
    return Blambda_val


def planckInvert(wavel, Blambda):
    """input wavelength in m and Blambda in W/m^2/m/sr, output
    output brightness temperature in K
    """
    Tbright = c2 / (wavel * np.log(c1 / (wavel**5. * Blambda) + 1.))
    return Tbright


def test_planck_wavelen():
    """
       test planck function for several wavelengths
       and Temps
    """
    #
    # need Temp in K and wavelen in m
    #
    the_temps = [200., 250., 350.]
    the_wavelens = np.array([8., 10., 12.]) * 1.e-6
    out = []
    for a_temp in the_temps:
        for a_wavelen in the_wavelens:
            #
            # convert to W/m^2/micron/sr
            #
            the_bbr = Blambda(a_wavelen, a_temp) * 1.e-6
            out.append(the_bbr)
    answer = [0.4521,   0.8954,   1.1955,   2.7324,   3.7835,   3.9883,
              21.4495,  19.8525,  16.0931]
    np.testing.assert_array_almost_equal(out, answer, decimal=4)
    return None


def test_planck_inverse():
    """
       test planck inverse for several round trips
       and Temps
    """
    #
    # need Temp in K and wavelen in m
    #
    the_temps = [200., 250., 350.]
    the_wavelens = np.array([8., 10., 12.]) * 1.e-6
    out = []
    for a_temp in the_temps:
        for a_wavelen in the_wavelens:
            #
            # convert to W/m^2/micron/sr
            #
            the_bbr = Blambda(a_wavelen, a_temp)
            out.append((a_wavelen, the_bbr))

    brights = []
    for wavelen, bbr in out:
        brights.append(planckInvert(wavelen, bbr))
    answer = [200.0, 200.0, 200.0, 250.0, 250.0, 250.0, 350.0, 350.0, 350.0]
    np.testing.assert_array_almost_equal(brights, answer, decimal=10)
    return None


if __name__ == "__main__":
    #
    # the variable __file__ contains the name of this file
    # so the result of the following line will be the same as if
    # you typed:
    #
    # pytest ~/pythonlibs/a301lib/radiation.py -q
    #
    # in a terminal  (the -q means 'suppress most of output')
    #
    print('testing {}'.format(__file__))
    pytest.main([__file__, '-q'])
