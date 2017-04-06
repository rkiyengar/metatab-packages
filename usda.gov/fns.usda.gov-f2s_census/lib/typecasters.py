
def parse_counts(v):
    from rowpipe.valuetype import robust_int
    
    if not v or v == '.':
        return None
        
    return robust_int(v)
        
def parse_pct(v):
    from rowpipe.valuetype import robust_int
    
    if not v or v == '.':
        return None
        
    return float(v)