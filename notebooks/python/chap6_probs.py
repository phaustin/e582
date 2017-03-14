
# coding: utf-8

# ### Chapter 6 thermo answers

# In[3]:

import e582lib.radiation as rad


# ### problem 6.8

# In[4]:

Blambda=6.2e6 #W/m^2/sr/m
wavel=12e-6 #meters
Tb = rad.planckInvert(wavel, Blambda)
print('the brightness temperature is {:6.3f} K'.format(Tb))


# In[6]:

eps=0.9
bbody_rad=Blambda/eps
Tb_kinetic=rad.planckInvert(wavel, bbody_rad)
print('kinetic temperture = {:6.3f} K'.format(Tb_kinetic))
print('temperature ratio = {:5.2f}'.format(Tb/Tb_kinetic))


# ### problem 6.9

# In[7]:

Blambda = 2.103e-4  #W/m^2/sr/m
wavel=1.e-2  #meters
Tb = rad.planckInvert(wavel, Blambda)
print('the brightness temperature is {:6.3f} K'.format(Tb))


# In[8]:

eps=0.9
bbody_rad=Blambda/eps
Tb_kinetic=rad.planckInvert(wavel, bbody_rad)
print('kinetic temperature = {:6.3f} K'.format(Tbnew))
print('temperature ratio = {:5.2f}'.format(Tb/Tb_kinetic))


# In[ ]:



