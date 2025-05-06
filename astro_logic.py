from skyfield.api import load, Star, load_constellation_names
import pandas as pd
import os

ephemeris = load('de421.bsp')
earth = ephemeris['earth']

def load_star_catalog(filepath):
    """Load star catalog from CSV file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Star catalog not found at: {filepath}")
    
    try:
        df = pd.read_csv(filepath)
        required_columns = ['name', 'ra', 'dec', 'mag']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        return df
    except pd.errors.EmptyDataError:
        raise ValueError("Star catalog file is empty")
    except pd.errors.ParserError as e:
        raise ValueError(f"Error parsing star catalog: {e}")

def get_star_position(star_data, observer, time):
    """Calculate star position for given time and location."""
    try:
        star = Star(ra_hours=star_data['ra'], dec_degrees=star_data['dec'])
        # Create observation from earth + observer's position at specific time
        observation = (earth + observer).at(time)
        # Calculate star's position from the observation point
        astrometric = observation.observe(star)
        alt, az, distance = astrometric.apparent().altaz()
        return az.degrees, alt.degrees
    except Exception as e:
        raise ValueError(f"Error calculating star position: {e}")

def calculate_star_positions(catalog, observer, time):
    """Calculate positions for all stars in catalog."""
    positions = []
    for _, star in catalog.iterrows():
        try:
            az, alt = get_star_position(star, observer, time)
            positions.append({
                'name': star['name'],
                'az': az,
                'alt': alt,
                'mag': star['mag']
            })
        except Exception as e:
            print(f"Warning: Could not calculate position for star {star['name']}: {e}")
            continue
    return positions
