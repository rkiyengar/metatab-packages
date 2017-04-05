

def star_is_not_a_number(v):
    
    
    try:
        if str(v).strip()[0] == '*':
            return None
        else:
            return v
    except IndexError:
        return None
