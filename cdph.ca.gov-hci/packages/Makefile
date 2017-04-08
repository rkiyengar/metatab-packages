
# FOr Python 2.7.9 and Python 3.5 if you get ssl.CertificateError, add this to the boto
# config file: 
# [s3]
# calling_format = boto.s3.connection.OrdinaryCallingFormat

S3_BUCKET = library.metatab.org

SOURCES = $(shell ls *.csv)
PACKAGE_NAMES = $(patsubst %.csv,%,$(SOURCES))

#dest= $(PACK_NAME).zip $(PACK_NAME).xlsx $(PACK_NAME)/index.html $(PACK_NAME).s3

#_DESTS=$(patsubst %,%.zip,$(PACKAGE_NAMES)) $(patsubst %,%.xlsx,$(PACKAGE_NAMES)) $(patsubst %,%.s3,$(PACKAGE_NAMES))
_DESTS=$(patsubst %,%.s3,$(PACKAGE_NAMES))
DESTS= $(sort $(_DESTS))

all: $(DESTS)


%.zip: %.csv
	metapack -z $<
	s3put -b $(S3_BUCKET) -k zip -p $(shell pwd) $@
	
%.xlsx: %.csv
	metapack -e $<
	s3put -b $(S3_BUCKET) -k xlsx -p $(shell pwd) $@

%/index.html: %.csv
	metapack -f $<
	
%.s3: %.csv
	metasync -S s3://$(S3_BUCKET) $<
	touch $@