'''
*-------------------------------------------------------------------------
* $Id: emiss.f,v 1.4 2002/10/03 22:27:00 phil Exp $
*  Reference:
*
*       Petty, 1990: "On the Response of the Special Sensor Microwave/Imager
*         to the Marine Environment - Implications for Atmospheric Parameter
*         Retrievals"  Ph.D. Dissertation, University of Washington, 291 pp.
*      (Journal articles pending)
*
*   coded in a quick-and-dirty fashion, and without any warranty, by:
*   Grant W. Petty
*   Earth and Atmospheric Sciences Dept.
*   Purdue University
*   West Lafayette, IN  47907
*   USA
*
*   Tel. No. (317) 494-2544
*   Internet address : gpetty@rain.atms.purdue.edu
*
*----------------------------------------------------------------------

Converted to Python 2.7 code by Yingkai (Kyke) Sha
    yingkai@eos.ubc.ca
    
'''

import numpy as np

def emiss(ifreq, speed, sst, theta):
    '''
    *
    *   INPUT:
    *
    *   ifreq = 1 (19.35)        speed = wind speed (m/s)
    *           2 (22.235)       sst   = sea surface temperature in kelvin
    *           3 (37.0)         theta = view angle of satellite in degrees
    *           4 (85.5)
    *
    *   OUTPUT:
    *
    *           emissh = horizontally polarized emissivity
    *           emissv = vertically polarized emissivity
    *
    '''
    #implicit none
    #real*4 ebiasv(4),ebiash(4),cf(4),cg(4),emissv,emissh
    #real*4 theta,sst,speed,fem,foam,gx2,remv,remh
    #integer ifreq
    cf = np.array([0.008,0.008,0.008,0.008])
    cg =  np.array([3.49e-3, 3.60e-3, 4.85e-3, 6.22e-3])
    # empirical bias corrections for surface emissivity
    #data ebiasv /0.00400,-0.00451,-0.0124,-0.00189/
    #data ebiash /0.00354,     0.0,-0.0125, 0.05415/
    ebiasv = np.array([0.00,0.00,0.0,0.00])
    ebiash = np.array([0.00,0.00,0.0,0.00])
    #* 'foam' emissivity
    fem = 1.0
    #
    #* SST adjustment (not part of Petty's original code)
    #
    if(sst < 271.25):
        sst = 271.25

    #* effective surface slope variance
    gx2 = cg[ifreq-1]*speed

    #* get rough surface emissivity

    remv, remh = roughem(ifreq, gx2, sst, theta)
    #print('remv: {}, remh: {}'.format(remv, remh))
    #remv=1.
    #remh=1.

    #* compute 'foam' coverage

    if(speed > 7.0):
        foam = cf[ifreq-1]*(speed-7.0)
    else:
        foam = 0.0

    #* compute surface emissivities and reflectivity

    emissv = foam*fem + (1.0 - foam)*(remv + ebiasv[ifreq-1])
    emissh = foam*fem + (1.0 - foam)*(remh + ebiash[ifreq-1])
    return emissv, emissh 

#*================================================================
def roughem(ifreq, gx2, tk, theta):
    '''
    *
    * Calculates rough-surface emissivity of ocean surface at SSM/I
    * frequencies.
    *
    '''
    #implicit none
    #real a19v(4),a22v(4),a37v(4),a85v(4)
    #real a19h(4),a22h(4),a37h(4),a85h(4)
    #real f(4),tp,tk,dtheta,theta,g,x1,x2,x3,x4,remv,remh
    #real gx2,semv,semh,ev,eh
    #integer ifreq
    #*
    a19v = np.array([  -0.111E+01,   0.713E+00,  -0.624E-01,   0.212E-01 ])
    a19h = np.array([   0.812E+00,  -0.215E+00,   0.255E-01,   0.305E-02 ])
    a22v = np.array([  -0.134E+01,   0.911E+00,  -0.893E-01,   0.463E-01 ])
    a22h = np.array([   0.958E+00,  -0.350E+00,   0.566E-01,  -0.262E-01 ])
    a37v = np.array([  -0.162E+01,   0.110E+01,  -0.730E-01,   0.298E-01 ])
    a37h = np.array([   0.947E+00,  -0.320E+00,   0.624E-01,  -0.300E-01 ])
    a85v = np.array([  -0.145E+01,   0.808E+00,  -0.147E-01,  -0.252E-01 ])
    a85h = np.array([   0.717E+00,  -0.702E-01,   0.617E-01,  -0.243E-01 ])
    #*
    f = np.array([ 19.35, 22.235, 37.0, 85.5 ])
    #*
    tp = tk/273.0
    dtheta = theta-53.0
    g =  0.5*gx2
    x1 = g
    x2 = tp*g
    x3 = dtheta*g
    x4 = tp*x3
    #*
    if (ifreq == 1):
        remv = x1*a19v[0] + x2*a19v[1] + x3*a19v[2] + x4*a19v[3]
        remh = x1*a19h[0] + x2*a19h[1] + x3*a19h[2] + x4*a19h[3]
    elif (ifreq == 2):
        remv = x1*a22v[0] + x2*a22v[1] + x3*a22v[2] + x4*a22v[3]
        remh = x1*a22h[0] + x2*a22h[1] + x3*a22h[2] + x4*a22h[3]
    elif (ifreq == 3):
        remv = x1*a37v[0] + x2*a37v[1] + x3*a37v[2] + x4*a37v[3]
        remh = x1*a37h[0] + x2*a37h[1] + x3*a37h[2] + x4*a37h[3]
    elif (ifreq == 4):
        remv = x1*a85v[0] + x2*a85v[1] + x3*a85v[2] + x4*a85v[3]
        remh = x1*a85h[0] + x2*a85h[1] + x3*a85h[2] + x4*a85h[3]
        
    semv, semh = spemiss(f[ifreq-1], tk, theta, 36.5)
    #print('semv: {}, semh: {}'.format(semv, semh))
    remv = remv + semv
    remh = remh + semh
    return remv, remh
      
#********************

def epsalt(f,t, ssw):
    '''
    *     returns the complex dielectric constant of sea water, using the
    *     model of Klein and Swift (1977)
    *
    *     Input   f = frequency (GHz)
    *             t = temperature (C)
    *             ssw = salinity (permil) (if ssw < 0, ssw = 32.54)
    *     Output  epsr,epsi  = real and imaginary parts of dielectric constant
    *
    '''
    #implicit none
    #real*4 f,t,epsr,epsi,pi,ssw,ssw2,ssw3,t2,t3,es,a,tau
    #real*4 delt,delt2,beta,om,b,sig,epsrhold,epsihold
    #complex cdum1,cdum2,cdum3,cmplx
    #parameter (pi = 3.14159265)
    #*
    if (ssw < 0.0):
        ssw = 32.54
    ssw2 = ssw*ssw
    ssw3 = ssw2*ssw
    t2 = t*t
    t3 = t2*t
    es = 87.134 - 1.949e-1*t - 1.276e-2*t2 + 2.491e-4*t3
    a = 1.0 + 1.613e-5*ssw*t - 3.656e-3*ssw + 3.21e-5*ssw2 - 4.232e-7*ssw3
    es = es*a
    #*
    tau = 1.768e-11 - 6.086e-13*t + 1.104e-14*t2 - 8.111e-17*t3
    b = 1.0 + 2.282e-5*ssw*t - 7.638e-4*ssw - 7.760e-6*ssw2 + 1.105e-8*ssw3
    tau = tau*b
    #*
    sig = ssw*(0.182521 - 1.46192e-3*ssw + 2.09324e-5*ssw2 - 1.28205e-7*ssw3)
    delt = 25.0 - t
    delt2 = delt*delt
    beta = 2.033e-2 + 1.266e-4*delt + 2.464e-6*delt2 - ssw*(1.849e-5 - 2.551e-7*delt + 2.551e-8*delt2)
    sig = sig*np.exp(-beta*delt)
    #*
    om = 2.0e9*np.pi*f
    cdum1 = 0.0 + 1.0j*om*tau #cmplx(0.0,om*tau)
    cdum2 = 0.0 + 1.0j*sig/(om*8.854e-12) #cmplx(0.0,sig/(om*8.854e-12))
    cdum3 = 4.9 + (es-4.9)/(1.0 + cdum1) - cdum2
    epsrhold = cdum3.real #real(cdum3)
    epsihold = -1*cdum3.imag #-aimag(cdum3)
    epsi=0.5
    epsr=0.5
    if (epsrhold > 1.):
        epsr=epsrhold
    if (epsihold > 1.):
        epsi=epsihold
    #print('epsr: {}, epsi: {}'.format(epsr, epsi)) #print *,"in epsalt III",epsr," test ",epsi
    #epsi=1.
    #epsr=1.
    return epsr, epsi

#**************************************

def spemiss(f, tk, theta, ssw):
    '''
    *     returns the specular emissivity of sea water for given freq. (GHz), 
    *     temperature T (K), incidence angle theta (degrees), salinity (permil)
    *     
    *     Returned values verified against data in Klein and Swift (1977) and
    *     against Table 3.8 in Olson (1987, Ph.D. Thesis)
    *
    '''
    from numpy.lib.scimath import sqrt as csqrt
    #implicit none
    #real*4 f,tk,theta,ssw,ev,eh
    #real*4 fold,tkold,sswold,epsr,epsi,epsrold,epsiold
    #save fold,tkold,sswold,epsrold,epsiold
    #*
    #real*4 tc,costh,sinth,rthet
    #complex*8 etav,etah,eps,cterm1v,cterm1h,cterm2,cterm3v,cterm3h
    #*
    # <------------ !!! This section has been modified
    #if ((f != fold) | (tk != tkold) | (ssw < sswold)):
    #    tc = tk - 273.15
    #    fold = f
    #    tkold = tk
    #    sswold = ssw
    tc = tk - 273.15
    epsr, epsi = epsalt(f, tc, ssw)
    epsrold = epsr
    epsiold = epsi
    #else:
    #epsr = epsrold
    #epsi = epsiold

    eps = epsr + 1.0j*epsi #cmplx(epsr,epsi)
    etav = eps
    etah = 1.0+1.0j*0.0 #(1.0, 0.0)
    rthet = theta*0.017453292
    costh = np.cos(rthet)
    sinth = np.sin(rthet)
    sinth = sinth*sinth
    cterm1v = etav*costh
    cterm1h = etah*costh
    eps = eps - sinth
    cterm2 = csqrt(eps) # <---------- csqrt
    cterm3v = (cterm1v - cterm2)/(cterm1v + cterm2)
    cterm3h = (cterm1h - cterm2)/(cterm1h + cterm2)
    #print('cterm3v: {}, cterm3h: {}'.format(cterm3v, cterm3h))
    ev = 1.0 - np.abs(cterm3v)**2 #cabs(cterm3v)**2
    eh = 1.0 - np.abs(cterm3h)**2 #cabs(cterm3h)**2
    return ev, eh
    
def coef(SST):
    '''   
    C     $Id: coef.f,v 1.2 2002/10/03 19:56:26 phil Exp $
    C*    This subroutine calculates the absorption coefficients and
    c     the oxygen transmission at 19 and 37 GHz given the SST and
    c     parameterizing the effective cloud emission temperature.
    c
    c     INPUT:
    C                SST   -  Sea surface temperature in Kelvin (for a
    c                         particular grid box)
    c     OUTPUT:
    C                KL19  -  Liquid water absorption coefficient at 19 GHz
    c                KL37  -  Liquid water absorption coefficient at 37 GHz
    c                KV19  -  Water vapor absorption coefficient at 19 GHz
    c                KV37  -  Water vapor absorption coefficient at 37 GHz
    C                TOX19 -  Oxygen transmission at 19 GHz
    C                TOX37 -  Oxygen transmission at 37 GHz
    c
    ========================================================================
    Converted to Python 2.7 code by Yingkai (Kyke) Sha
    yingkai@eos.ubc.ca
    '''
    #implicit none
    #REAL*4 SST,KL19,KL37,KV19,KV37,TOX19,TOX37
    #real*4 TC,TCEL,TSCEL

    #C  Set effective cloud emission temp
    TC = SST - 6.
    #C  Compute liquid water mass absorption coefficients (m**2/kg)
    #C  From Petty Ph.D. dissertation, 1990
    TCEL = TC - 273.15
    #c
    KL19 = 0.0786 - 0.230E-2*TCEL + 0.448E-4*TCEL**2 - 0.464E-6*TCEL**3
    KL37 = 0.267 - 0.673E-2*TCEL + 0.975E-4*TCEL**2 - 0.724E-6*TCEL**3
    #c
    TSCEL = SST - 273.15
    #c
    TOX19 = 0.9779 -6.314E-5 * TSCEL + 7.746E-6 * TSCEL**2 - 1.003E-7 * TSCEL ** 3
    TOX37 = 0.9269 -8.525E-5 * TSCEL + 1.807E-5 * TSCEL**2 - 2.008E-7 * TSCEL ** 3
    KV19 = 2.58E-3 * (300./SST)**0.477
    KV37 = 2.12E-3
    return KL19, KL37, KV19, KV37, TOX19, TOX37