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

### caNanoAPISampleReport.py, caNanoSampleReport.py
These two scripts generate a report for each caNano sample that includes the composition, characterization, and publication information for the sample.  **caNanoAPISampleReport.py** is the long-term solution as it will get the information from the GC API instead of a spreadsheet.

### caNanoSampleReportSkill.md
An attempt at a Claude skill file with instructions to generate a sample report using the GC API.

### DataCiteUpdate.py
Probably obsolete, was intended to update DataCite entries

### DCFFileCheck.py
A script that tests using a GC File ID as the start and works through getting a signed URL from DCF.

### DOIJSONCheck.py
A QA script that makes sure the right DOI ended up on the right html page

### DOIUpdated.py
This script was used to update the DOI records for caNano to point to NCI.  Not sure it has much use after the transfer is complete

### Excel2JSON.py
A script that generates a JSON object for updating DOIs.  It never did work and **DataCiteUpdate.py** should be used instead.

### Excel2Markdown.py
This script performs the same function as Excel2HTML except that the generated files are in Markdown, not HTML.  This was abandonded because the DataCite spec for DOI pages requires the presence of information using <meta> tags and GitHub Pages doesn't have a way to include those from Markdown.

### FileInfoMachine.py
Hits the GC API to collect file information.  Originally part of the sample report, but not used.

### GCAPI2HTML.py
This is the production version of **Excel2HTML.py**. This writes the individual DOI pages, but uses the GC API to get caNano metadata.

*Usage*: python3 -c <configuration_file> -v <verbosity>

#### Configuration options
- **writedir**: A directory where the individual doi and index HTML pages will be written. \
- **sqlitefile**: Name of the sqlite database file.  This should be in the directory specified in **writedir** \
- **scope**: The scope of the HTML file generation.  Allowed values are: \
-- *all*:  Generate all of the doi pages and index pages.  This also resets the database. \
-- *new*: Generate only new doi pages.  New pages are any pages not present in the database. \
-- *index*: Generate only a new index.html page.  This will read the existing database for individual page information. \

