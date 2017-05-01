
def split_range_lower(rng):
    
    parts = str(rng).split()
    
    if len(parts) != 3:
        return None
        
    if parts[2].strip() == 'less':
        return 0
        
    return int(parts[0].replace(',',''))
  
    
def split_range_upper(rng):
    
    parts = str(rng).split()

    if len(parts) != 3:
        return None
        
    if parts[2] == 'less':
        return int(parts[0].replace(',',''))
        
    if parts[2] == 'more':
        return None
        
    return int(parts[2].replace(',',''))