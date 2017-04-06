
# FOr Python 2.7.9 and Python 3.5 if you get ssl.CertificateError, add this to the boto
# config file: 
# [s3]
# calling_format = boto.s3.connection.OrdinaryCallingFormat


#
# 
METAKAN_S3_URL ?= s3://library.metatab.org
S3_BUCKET= $(subst s3://,,$(METAKAN_S3_URL))
METAKAN_CKAN_URL ?=  http://data.sandiegodata.org/ 
PACK_NAME=$(shell metapack -n)

dest= $(PACK_NAME).zip 

all: $(dest)

# Makes excel and zip, but only depends for zip
%.zip: metadata.csv
	metakan --s3url $(METAKAN_S3_URL) --ckanurl $(METAKAN_CKAN_URL)   -z -e -s3
    
    