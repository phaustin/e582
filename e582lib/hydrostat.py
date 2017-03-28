import numpy as np

def hydrostat(T_surf,p_surf,dT_dz,delta_z,num_levels):
    """
    build a hydrostatic atmosphere by integrating the hydrostatic equation from the surface,
    using num_layers=num_levels-1 of constant thickness delta_z

    Parameters
    ----------
    T_surf: float
        surface temperature in K
    p_surf: float
       surface pressure in Pa
    dT_dz: float
        constant rate of temperature change with height in K/m
    delta_z: float
        layer thickness in m
    num_levels: float
       number of levels in the atmosphere


    Returns
    -------
    tuple of numpy arrays: tuple for float vectors of lenght numlevels - 1
         Temp (K) , press (Pa), rho (kg/m^3), height (m)
    """
    Rd=287. #J/kg/K  -- gas constant for dry air
    g=9.8  #m/s^2
    Temp=np.empty([num_levels])
    press=np.empty_like(Temp)
    rho=np.empty_like(Temp)
    height=np.empty_like(Temp)
    #
    # layer 0 sits directly above the surface, so start
    # with pressure, temp of air equal to ground temp, press
    # and get density from equaiton of state
    # 
    press[0]=p_surf
    Temp[0]=T_surf
    rho[0]=p_surf/(Rd*T_surf)
    height[0]=0
    num_layers=num_levels-1
    #now march up the atmosphere a layer at a time
    for i in range(num_layers):
        delP= -rho[i]*g*delta_z
        height[i+1] = height[i] + delta_z
        Temp[i+1] = Temp[i] + dT_dz*delta_z
        press[i+1]= press[i] + delP
        rho[i+1]=press[i+1]/(Rd*Temp[i+1])
    return (Temp,press,rho,height)
