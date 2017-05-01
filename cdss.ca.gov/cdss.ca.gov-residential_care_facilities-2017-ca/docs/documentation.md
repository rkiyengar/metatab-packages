

## Processing

RCFE Factilities are geocoded to tracts using the [Census geocoder](https://www.census.gov/geo/maps-data/data/geocoder.html), which fails to geocode about 5 percent of the RCFE addresses. The facilities that fail to geocode are assigned to tracts with the following procedure

- Using the [HUD Zip to Tract crosswalk](https://www.huduser.gov/portal/datasets/usps_crosswalk.html), all of the tracts that overlap with the zip code for a facility are collected. 
- THe list of tracts is sorted and a cumultative sum of the proportion of the residential addresses of the zip assigned to each tract is computed.
- The last two digits of the facility id are divided by 100 to produce a number from 0 to 99. 
- That number is used to index the cumulative sum list to select a tract. 

The result of this procedure is that a set of RCFE, all from the same zip code, will be assigned to tracts in the same proportion that residences in the zip code are assigned to tracts. 