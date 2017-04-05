# Metatab Packages

Data Packages in Metatab format

This repository holds [Metatab](http://metatab.org) files for data packages for which we don't control the data -- all of the resource URLs are off site. You can use the metatab files to create local data packages with the [metapack](https://github.com/CivicKnowledge/metapack) application.

For a guide to getting started using the metatab programs, see the tutorial for the [Metatab Python module.](https://github.com/CivicKnowledge/metatab-py)

## Creating Packages In This Repo

After cloning this repo, the typical process is:

1. Create a subdirectory for the data origin
2. In the origin directory, create a new `metadata.csv` file.
3. Update the name elements in the metadata, and regenerate the name. 
4. Create a new directory with the dataset name, excluding the version. 
5. Move the `metadata.csv` file into the new dataset directory. 

For example, to create the dataset for the [California School Dashboard](http://www.cde.ca.gov/ta/ac/cm/)

```bash
$ mkdir cde.ca.gov
$ metapack -c
```

Open the `metadata.csv` file and make these changes:

```
Name.Dataset: accountability-dashboard
Name.Origin: cde.ca.gov
```

Then save the file and run: 

```bash
$ metapack -u 
Changed Name
Name is:  cde.ca.gov-accountability_dashboard-1
$ mkdir cde.ca.gov/cde.ca.gov-accountability_dashboard
$ mv metadata.csv cde.ca.gov/cde.ca.gov-accountability_dashboard
```
