import numpy as np

def rolling_resistance():
    """
    Returns the coefficient of rolling resistance for cycling.

    Returns:
    float: Coefficient of rolling resistance (typical value: 0.0050).
    """
    return 0.0050

def gravity(slope, weight):
    """
    Calculates the gravitational force component for cycling.

    Args:
    slope (float): Slope of the road (in percentage).
    weight (float): Total weight of the cyclist and the bicycle (in kg).

    Returns:
    float: Gravitational force.
    """
    return 9.80665 * np.sin(np.arctan(slope)) * (weight + 6.8)

def aerodynamic_drag(v):
    """
    Calculates the aerodynamic drag force for cycling.

    Args:
    v (float): Velocity of the cyclist (in meters per second).

    Returns:
    float: Aerodynamic drag force.
    """
    cda = 0.3
    elevation = 375
    p = (1.225* np.exp(-0.00011856*elevation))
    w = 0
    return 0.5 * cda * p * (v + w)**2

def cycling_power(slope, weight, velocity):
    """
    Calculates the cycling power required.

    Args:
    slope (float): Slope of the road (in percentage).
    weight (float): Total weight of the cyclist and the bicycle (in KG).
    velocity (float): Velocity of the cyclist (in meters per second).

    Returns:
    float: Cycling power required (in Watts).
    """
    Fg = gravity(slope, weight)
    Fr = rolling_resistance()
    Fa = aerodynamic_drag(velocity)
    return ((Fg + Fr + Fa) * velocity) / (1-0.03)

# Adjust power based on stage profile
def cycling_power_profile(slope, weight, velocity, profile):
    """
    Adjusts cycling power based on the stage profile.

    Args:
    slope (float): Slope of the road (in percentage).
    weight (float): Total weight of the cyclist and the bicycle (in KG).
    velocity (float): Velocity of the cyclist (in meters per second).
    profile (str): Stage profile identifier ('p1' to 'p5').

    Returns:
    float: Adjusted cycling power based on the stage profile (in Watts).
    """
    if profile == 'p1': # Flat
        return cycling_power(slope, weight, velocity)
    if profile == 'p2': # Hills, flat finish
        return np.mean((cycling_power(slope, weight, velocity * 0.75),
                        cycling_power(0, weight, velocity)))
    if profile == 'p3': # Hills, uphill finish
        return np.mean((cycling_power(slope, weight, velocity * 0.75),
                        cycling_power(0, weight, velocity * 1)))
    if profile == 'p4': # Mountains, flat finish
        return np.mean((cycling_power(slope*4, weight, velocity * 0.66),
                        cycling_power(0, weight, velocity)))
    if profile == 'p5': # Mountains, uphill finish
        return np.mean((cycling_power(slope*4, weight, velocity * 0.75),
                        cycling_power(0, weight, velocity)))
    