# caNanoLabDOI

Scripts for caNanoLab DOI pages

## Background

The caNanoLab project moved to NCI and as a result there is a need to support the DOIs that caNanoLab creates and uses.  The decision was to use GitHub Pages to be the DOI landing pages and the scripts in this repository will generate those pages.

## Scripts

### Excel2HTML.py

This script reads and Excel file containing caNanoLab data (for now, will be moved to GC API when caNanoLab data are loaded) and a YAML configuration file and generates an HTML page for each DOI.  It also generates an index.html page that lists all the pages that have been created.

*Usage:* python3 Excel2HTML.py -c \<configuration file> -v \<verbosity>

#### Config file options:

**xlfile**: Full path and filename of the Excel file containing caNanoLab data. \
**sheet**: A list of sheets in the Excel file. \
**writedir**: A directory where the individual doi and index HTML pages will be written. \
**scope**: The scope of the HTML file generation.  Allowed values are: \

- *all*:  Generate all of the doi pages and index pages.  This also resets the database. \
- *new*: Generate only new doi pages.  New pages are any pages not present in the database. \
- *index*: Generate only a new index.html page.  This will read the existing database for individual page information. \

**sqlitefile**: The name of the sqlite database file to use.  This will be saved in teh directory specified by **writedir**. \

### Excel2Markdown.py

This script performs the same function as Excel2HTML except that the generated files are in Markdown, not HTML.  This was abandonded because the DataCite spec for DOI pages requires the presence of information using <meta> tags and GitHub Pages doesn't have a way to include those from Markdown.
