# Reads the Excel file from ISB and creates a markdown page for each line
import pandas as pd
import numpy as np
import argparse
import yaml
import os
import sqlite3


header = "# caNanoLab DOI \n"
separator = "-------------------------- \n"
tableheader = "| Property | Value | \n"
tableseparator = "|----------|---------| \n"
fileheader = "| DOI | Protocol Name | \n"
fileseparator = "|----------|---------|  \n"

gcurl = "https://general.datacommons.cancer.gov/#/data"


# General TODO:
# Write GraphQL query for GC once data model goes live
# Might need a new filenaming convention, this is based on data that GC may not use

def readYAML(yamlfile):
    with open(yamlfile) as f:
        yamljson = yaml.load(f, Loader=yaml.FullLoader)
    return yamljson



def readXL(xlfile, sheetlist):
    df_collection = {}
    for sheet in sheetlist:
        temp_df = pd.read_excel(xlfile, sheet_name=sheet)
        df_collection[sheet] = temp_df
    return df_collection


def sampleRows(sampleID, sample_df):
    sampleID = str(sampleID)
    returnthings = []
    if "|" in sampleID:
        samplelist = sampleID.split("|")
    else:
        samplelist = [sampleID]
    for sample in samplelist:
        sample = int(sample)
        temp_df = sample_df.query('sample_id == @sample')
        for index, row in temp_df.iterrows():
            returnthings.append({"id":row['sample_id'], "name": row['Sample_Name'], "org": row['Organization_Name']})
    return returnthings


def charDataRows(sampleID, char_df):
    sampleID = str(sampleID)
    returnthings = []
    if "|" in sampleID:
        samplelist = sampleID.split("|")
    else:
        samplelist = [sampleID]
    for sample in samplelist:
        sample = int(sample)
        temp_df = char_df.query('parentSampleID == @sample')
        for index, row in temp_df.iterrows():
            returnthings.append({'cid': row['characterization_id'], 'type': row['characterization_type'], 'assay':[row['assay_type']]})
    return returnthings


def compDataRow(sampleID, comp_df):
    sampleID = str(sampleID)
    returnthings = []
    if "|" in sampleID:
        samplelist = sampleID.split("|")
    else:
        samplelist = [sampleID]
    for sample in samplelist:
        sample = int(sample)
        temp_df = comp_df.query('parentSampleID == @sample')
        for index, row in temp_df.iterrows():
            returnthings.append({'type': row['nanomaterial_entity']})
    return returnthings


def fileRowData(longfilename, file_df):
    returnthings = []
    filename = longfilename.split("/")[-1]
    temp_df = file_df.query('file_name == @filename')
    for index, row in temp_df.iterrows():
        returnthings.append({"name": row['file_name'], "type": row['file_type']})
    return returnthings



def pullKnownFiles(df, cursor):
    known = []
    seriieslist = []
    main_df = df['Protocol']

    for row in cursor.execute("SELECT filename FROM fileinfo "):
        known.append(row[0])
    for index, row in main_df.iterrows():
        if f"{row.protocol_pk_id}.md" not in known:
            seriieslist.append(row)
    new_df = pd.DataFrame(seriieslist)
    df['Protocol'] = new_df
    return df

def deleteTest(cursor, conn):
    cursor.execute("DELETE FROM fileinfo WHERE filename LIKE '11413115%'")
    conn.commit()


def writeDOIFiles(doi_df, writedir, logo):

    main_df = doi_df['Protocol']
    dbdata = []

    for index, row in main_df.iterrows():
        if row['doi'] is not np.nan:
            outfile = f"{writedir}{row['protocol_pk_id']}.md"
            with open(outfile, 'w') as f:
                url = f"http://dx.doi.org/{row.doi}"
                dbdata.append((row.protocol_name, f"{row.protocol_pk_id}", 'Protocol', row.doi))
                f.write(logo)
                f.write(header)
                f.write(separator)
                f.write(f"**Protocol Type:**\t{row.protocol_type} \n")
                f.write(f"**Protocol Name:**\t{row.protocol_name} \n")
                f.write(f"**Protocol Abbreviation:**\t{row.protocol_abbreviation} \n")
                f.write(f"**Protocol Version:**\t{row.protocol_version} \n")
                f.write(separator)
                f.write(f"**DOI:**\t{url}")
                f.write(f"**Protocol File:**\t{row.file_name}")
                f.write(f"**File Title:**\t{row.title}")
                f.write(f"**Description:**\t{row.description}")
                f.write(separator)
                f.write("**Resource Type:**\tProtocol")
                f.write(f"**Data Access:**\t{gcurl}")
                f.close()
    return dbdata




def writeIndexFile(cursor, writedir, logo):
    indexfilename = f"{writedir}index.md"
    with open(indexfilename, 'w') as r:
        r.write(logo)
        r.write("## Example Layout Pages) \n")
        r.write(separator)
        r.write("[Table Example](./demopage-table.md)  \n")
        r.write("[Text Example](./demopage-text.md)  \n")
        r.write("[NCI Logo](./demopage-table-NCILogo.md)  \n")
        r.write("[caNano Logo](./demopage-table-caNanoLogo.md)  \n")
        r.write("[General Commons Logo](./demopage-table-GCLogo.md)  \n")
        r.write("# caNanoLab DOI Repository \n")
        r.write(separator)
        r.write("This repository contains the DOI landing pages for the caNanoLab project. \n")
        r.write(" \n")
        r.write("## DOI Pages \n")
        r.write(separator)
        r.write(fileheader)
        r.write(fileseparator)
        for row in cursor.execute("SELECT title, filename, filetype, doi FROM fileinfo"):
            #r.write(f"| [{row[0]}](./{row[1]}) | {row[2]} | {row[3]} | \n")
            r.write(f"| [{row[3]}](./{row[1]}) | {row[0]} | \n")
        r.close()




def excelCheck(xlfile):
    doi_df = pd.ExcelFile(xlfile)
    print(doi_df.sheet_names)


def main(args):

    logo = "![General Commons Logo](./assets/images/crdc-logo.svg) \n"
    cursor = None

    if args.verbose >= 1:
        print("Reading configuration file")
    configs = readYAML(args.configfile)


    if args.verbose >- 1:
        print(f"Checking for sqlite file {configs['writedir']}{configs['sqlitefile']}")
    if os.path.isfile(f"{configs['writedir']}{configs['sqlitefile']}"):
        if args.verbose >=1:
            print("Datadase existing, establishing connection")
            conn = sqlite3.connect(f"{configs['writedir']}{configs['sqlitefile']}")
            cursor = conn.cursor()
    else:
        if args.verbose >= 1:
            print("No database found, creating a new one")
        conn = sqlite3.connect(f"{configs['writedir']}{configs['sqlitefile']}")
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE fileinfo(title, filename, filetype, doi)")



    if configs['scope'] == 'all':
        if args.verbose >= 1:
            print("Getting list of existing files")
        if args.verbose >= 1:
            print(f"Creating datafrom from {configs['xlfile']}")
        doi_df = readXL(configs['xlfile'], configs['sheet'])

        if args.verbose >= 1:
            print("Writing individual DOI files")
        dbdata = writeDOIFiles(doi_df, configs['writedir'], logo)
        cursor.executemany("INSERT INTO fileinfo VALUES(?,?,?,?)", dbdata)
        conn.commit()

        if args.verbose >=1:
            print("Writing index.md file")
        writeIndexFile(cursor, configs['writedir'], logo)


    elif configs['scope'] == 'new':
        #
        #
        #     FOR TESTING ONLY
        #
        deleteTest(cursor, conn)
        #
        #      FOR TESTING ONLY
        #
        if args.verbose >= 1:
            print("Building new  pagees")
        doi_df = readXL(configs['xlfile'], configs['sheet'])
        doi_df = pullKnownFiles(doi_df, cursor)
        dbdata = writeDOIFiles(doi_df, configs['writedir'], logo)
        cursor.executemany("INSERT INTO fileinfo VALUES(?,?,?,?)", dbdata)
        conn.commit()
        writeIndexFile(cursor, configs['writedir'], logo)


    elif configs['scope'] == 'index':
        if args.verbose >= 1:
            print('Generating a new index.md file')
        if args.verbose >=1:
            print("Writing index.md file")
        # TODO: Generate a new doi_file_list
        writeIndexFile(cursor, configs['writedir'], logo)


    else:
        print('Incorrect scope setting, must be one of "all", "new", or "index"')




if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--configfile", required=True,  help="Configuration file containing all the input info")
    parser.add_argument('-v', '--verbose', action='count', default=0, help=("Verbosity: -v main section -vv subroutine messages -vvv data returned shown"))

    args = parser.parse_args()

    main(args)
