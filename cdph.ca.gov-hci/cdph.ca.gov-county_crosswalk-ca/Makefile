
# FOr Python 2.7.9 and Python 3.5 if you get ssl.CertificateError, add this to the boto
# config file: 
# [s3]
# calling_format = boto.s3.connection.OrdinaryCallingFormat

S3_BUCKET = library.metatab.org
PACK_NAME=$(shell metapack -n)

dest= $(PACK_NAME).zip $(PACK_NAME).xlsx $(PACK_NAME)/index.html .$(PACK_NAME).s3

all: $(dest)

%.zip: metadata.csv
	metapack -z
	s3put -b $(S3_BUCKET) -k zip -p $(shell pwd) $(PACK_NAME).zip  
	
%.xlsx: metadata.csv
	metapack -e
	s3put -b $(S3_BUCKET) -k xlsx -p $(shell pwd) $(PACK_NAME).xlsx

%.html: metadata.csv
	metapack -f
	
%.s3: metadata.csv
	metapack --s3 s3://$(S3_BUCKET)
	touch .$(PACK_NAME).s3