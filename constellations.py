CONSTELLATIONS = {
    "Ursa Major": {
        "description": "The Great Bear - one of the most recognizable northern constellations.",
        "stars": ["Dubhe", "Merak", "Phecda", "Megrez", "Alioth", "Mizar", "Alkaid"]
    },
    "Orion": {
        "description": "The Hunter - easily recognized by Orion's Belt.",
        "stars": ["Betelgeuse", "Rigel", "Bellatrix", "Saiph", "Mintaka", "Alnilam", "Alnitak"]
    }
}

def get_constellation_center(star_names, star_positions):
    """Calculate center point of constellation."""
    xs, ys = [], []
    star_pos_dict = {star['name']: (star['az'], star['alt']) for star in star_positions}
    
    for star in star_names:
        if star in star_pos_dict:
            az, alt = star_pos_dict[star]
            xs.append(az)
            ys.append(alt)
    
    if xs and ys:
        return sum(xs)/len(xs), sum(ys)/len(ys)
    return 0, 0
