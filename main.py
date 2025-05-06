from astro_logic import load_star_catalog, calculate_star_positions
from gui import init_pygame, main_loop, SkyMap
from skyfield.api import load, Topos
from datetime import datetime
import os
import sys

def main():
    try:
        # Get base directory
        base_dir = os.path.dirname(os.path.abspath(__file__))
        catalog_path = os.path.join(base_dir, 'data', 'star_catalog.csv')
        
        # Initialize Pygame and GUI
        screen = init_pygame()
        sky_map = SkyMap()
        
        # Load star catalog and initialize
        try:
            catalog = load_star_catalog(catalog_path)
            if catalog.empty:
                raise ValueError("Star catalog is empty")
            sky_map.catalog = catalog
            print(f"Loaded {len(catalog)} stars")  # Debug print
        except Exception as e:
            print(f"Error loading star catalog: {e}")
            sys.exit(1)
        
        # Set default time and location
        ts = load.timescale()
        sky_map.ts = ts
        sky_map.observer = Topos(latitude_degrees=52.0, longitude_degrees=21.0)
        sky_map.current_time = ts.now()
        
        # Calculate initial positions
        if sky_map.update_star_positions():
            print(f"Calculated positions for {len(sky_map.star_positions)} stars")  # Debug print
        else:
            print("Failed to calculate star positions")
        
        # Start the main loop
        main_loop(screen, sky_map)
        
    except Exception as e:
        print(f"An error occurred: {e}")
        print(f"Type of error: {type(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
