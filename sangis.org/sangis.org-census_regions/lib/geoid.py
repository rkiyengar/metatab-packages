
from geoid.acs  import Tract
def tract_geoid(row):
    """COnvert doted notation into a geoid """
    try:
        a,b = row['tract'].split('.')
    except ValueError:
        a = row['tract']
        b = '0'
    
    
    return Tract(6,73, int(a)*100+int(b.ljust(2,'0')))
   