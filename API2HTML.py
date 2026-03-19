# Read caNano data from the GC API and creates an HTML page for each entry
import pandas as pd
import numpy as np
import argparse
import yaml
import os
import requests
import json
import sqlite3
import sys


pageheader1 = '''<!DOCTYPE html>
<html lang="en">
    <head>
        <meta name="DC.IDENTIFIER" content="{}" scheme="DCTERMS.UI">'''


pageheader2 = """<title>caNanoLab DOI Landing page</title>
        <style>
            h1 { text-align: center;}
            h2 { text-align: left;}
            table { border: 1px solid #dddddd; text-align: left; padding: 8px }
            td, th { border: 1px solid #dddddd; text-align: left; padding: 8px }
            tr:nth-child(even) { background-color: #dddddd }
        </style>
    </head>"""

indexheader =  """<!DOCTYPE html>
<html lang="en">
    <head>
        <title>caNanoLab DOI Landing page</title>
        <style>
            h1 { text-align: center;}
            h2 { text-align: left;}
            table { border: 1px solid #dddddd; text-align: left; padding: 8px }
            td, th { border: 1px solid #dddddd; text-align: left; padding: 8px }
            tr:nth-child(even) { background-color: #dddddd }
        </style>
    </head>"""
gcurl = "https://general.datacommons.cancer.gov/#/data"

header = "<h1> caNanoLab DOI </h1>"
separator = "<hr>"

def readYAML(yamlfile):
    with open(yamlfile) as f:
        yamljson = yaml.load(f, Loader=yaml.FullLoader)
    return yamljson



'''def readXL(xlfile, sheetlist):
    df_collection = {}
    for sheet in sheetlist:
        temp_df = pd.read_excel(xlfile, sheet_name=sheet)
        df_collection[sheet] = temp_df
    return df_collection'''

def runBentoAPIQuery(url, query, variables=None):
    headers = {'accept': 'application/json'}
    try:
        if variables is None:
            results = requests.post(url, headers=headers, json={'query': query})
        else:
            results = requests.post(url, headers=headers, json={'query': query, 'variables': variables})
    except requests.exceptions.HTTPError as e:
        return (f"HTTPError:\n{e}")
        
    if results.status_code == 200:
        results = json.loads(results.content.decode())
        return results
    else:
        return (f"Error Code: {results.status_code}\n{results.content}")


def readAPI(apiurl):
    first = 10
    offset = 0
    getnext = True
    biglist = []
    query = """
        query getCaNano(
            $phs_accession: String!,
            $first: Int,
            $offset: Int
        )
        {
            protocols(phs_accession: $phs_accession, first: $first, offset: $offset){
                doi
                crdc_id
                file_id
                phs_accession
                protocol_name
                protocol_pk_id
                protocol_type
                sample_id
            }
        }
    """

    while getnext:
        vars = {"phs_accession": "10.17917", "first":first, "offset": offset}
        print(f"Vars:\t{vars}")
        results = runBentoAPIQuery(apiurl, query, vars)
        returncount = len(results['data']['protocols'])
        for result in results['data']['protocols']:
            biglist.append(result)
        if returncount < first:
            getnext = False
        else:
            offset = offset + first
    df = pd.DataFrame(biglist)
    return df


def getFileName(df, apiurl):

    filequery = '''
    query getFileInfo(
        $phs_accession: String!,
        $file_ids: [String!]
    ){
    files(
        phs_accession: $phs_accession,
        file_ids: $file_ids){
            file_description
            file_name
            file_type
            experimental_strategy_and_data_subtypes
            is_supplementary_file
            release_datetime
            file_id
        }
    }
    '''

    idlist = df['file_id'].unique().tolist()
    #tempidlist = [idlist[0], idlist[1], idlist[2]]
    #tempidlist = idlist[57:65]
    #print(tempidlist)
    fileinfo = []
    for id in idlist:
        filevars = {"phs_accession":"10.17917", "file_ids": id}
        filejson = runBentoAPIQuery(apiurl, filequery, filevars)
        #print(filejson)
        for entry in filejson['data']['files']:
            fileinfo.append(entry)
    file_df = pd.DataFrame(fileinfo)
    new_df = pd.merge(df, file_df, on=['file_id', 'file_id'])
    return new_df



def writeDOIFiles(doi_df, writedir, logo):

    #main_df = doi_df['Protocol']
    dbdata = []

    #for index, row in main_df.iterrows():
    for index, row in doi_df.iterrows():
        if row['doi'] is not np.nan:
            outfile = f"{writedir}{row['protocol_pk_id']}.html"
            with open(outfile, 'w') as f:
                url = f"http://dx.doi.org/{row.doi.strip()}"
                dbdata.append((row.protocol_name, f"{row.protocol_pk_id}", 'Protocol', row.doi.strip()))
                f.write(pageheader1.format(url))
                f.write(pageheader2)
                f.write("<body>")
                f.write(logo)
                f.write(header)
                f.write(separator)
                f.write("<p><b>Protocol Type:</b> {}</p>".format(row.protocol_type))
                f.write("<p><b>Protocol Name:</b> {}</p>".format(row.protocol_name))
                #f.write("<p><b>Protocol Abbreviation:</b> {}</p>".format(row.protocol_abbreviation))
                #f.write("<p><b>Protocol Version:</b> {}".format(row.protocol_version))
                f.write(separator)
                f.write("<p><b>DOI:</b> <a href = {}>{}</a></p>".format(url, url))
                f.write("<p><b>Protocol File:</b> {}".format(row.file_name))
                #f.write("<p><b>File Title:</b> {}</p>".format(row.title))
                f.write("<p><b>Description:</b></b> {}".format(row.file_description))
                f.write(separator)
                f.write("<p><b>Resource Type:</b>  Protocol</p>")
                f.write("<p><b>Data Access:</b> <a href ={}>{}</a><p>".format(gcurl, gcurl))
                f.write("</body>")
                f.write("</html>")
            f.close()
    return dbdata



def writeIndexFile(cursor, writedir, logo):
    indexfilename = f"{writedir}index.html"
    with open(indexfilename, 'w') as r:
        r.write(indexheader)
        r.write("<body>")
        r.write(logo)
        r.write("<h2>Example Layout Pages</h2>")
        r.write(separator)
        r.write("<table>")
        r.write("<tr>")
        r.write("<th>DOI</th>")
        r.write("<th>Title</th>")
        r.write("</tr>")
        for row in cursor.execute("SELECT title, filename, filetype, doi FROM fileinfo"):
            url = "https://cbiit.github.io/NCI-DOI-LandingPages/caNanoLab/{}".format(f"{row[1]}.html")
            r.write("<tr><td><a href={}>{}</a></td><td>{}</td></tr>".format(url, row[3], row[0]))
        r.write("</table")
        r.write("</body>")
        r.write("</html>")
        r.close()



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




def main(args):

    logo = '<img src="./assets/images/crdc-logo.svg" alt="CRDC General Commons Logo">'
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

        
    ###########################################
    #                                         #
    #                 ALL scope               #
    #                                         #
    ###########################################

    if configs['scope'] == 'all':
        if args.verbose >= 1:
            print("Scope is all pages")
            print("Getting list of existing files")
        doi_df = readAPI(configs['apiurl'])
        doi_df.replace("",np.nan, inplace=True)
        doi_df.dropna(subset=['doi'], inplace=True, axis=0)
        if args.verbose >= 1:
            print("Associating data with files")
        if args.verbose >= 2:
            print(doi_df.head())
        doi_df = getFileName(doi_df, configs['apiurl'])

        # Example file id:  dg.4DFC/a8243470-97fb-5b25-b438-e5bcbb726a1a
        #sys.exit(0)
        if args.verbose >= 1:
            print("Clearing existing database")
        cursor.execute("DELETE FROM fileinfo")
        if args.verbose >= 1:
            print("Writing individual DOI files")
        dbdata = writeDOIFiles(doi_df, configs['writedir'], logo)
        if args.verbose >= 1:
            print(f"Adding info to database {configs['sqlitefile']}")
        cursor.executemany("INSERT INTO fileinfo VALUES(?,?,?,?)", dbdata)
        conn.commit()

        if args.verbose >= 1:
            print("Writing index.html file")
        writeIndexFile(cursor, configs['writedir'], logo)

    ###########################################
    #                                         #
    #                 INDEX scope             #
    #                                         #
    ###########################################

    elif configs['scope'] == 'index':
        if args.verbose >= 1:
            print("Scope is index page only")
            print('Generating a new index.html file')
        writeIndexFile(cursor, configs['writedir'], logo)

    ###########################################
    #                                         #
    #                 NEW scope               #
    #                                         #
    ###########################################

    elif configs['scope'] == 'new':
        #
        #
        #     FOR TESTING ONLY
        #
        # deleteTest(cursor, conn)
        #
        #      FOR TESTING ONLY
        #
        if args.verbose >= 1:
            print("Scope is new pages only")
            print(f"Reading Excel file {configs['xlfile']}")
        #doi_df = readXL(configs['xlfile'], configs['sheet'])
        if args.verbose >= 1:
            print("Removing existing files")
        doi_df = pullKnownFiles(doi_df, cursor)
        if args.verbose >= 1:
            print("Writing new DOI files")
        dbdata = writeDOIFiles(doi_df, configs['writedir'], logo)
        if args.verbose >= 1:
            print(f"Updating database {configs['sqlitefile']} with new files")
        if args.verbose >= 2:
            print(f"Data Update:\n{dbdata}")
        cursor.executemany("INSERT INTO fileinfo VALUES(?,?,?,?)", dbdata)
        conn.commit()
        if args.verbose >= 1:
            print("Writing new index.html file")
        writeIndexFile(cursor, configs['writedir'], logo)

    else:
        print('Incorrect scope setting, must be one of "all", "new", or "index"')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--configfile", required=True,  help="Configuration file containing all the input info")
    parser.add_argument('-v', '--verbose', action='count', default=0, help=("Verbosity: -v main section -vv subroutine messages -vvv data returned shown"))

    args = parser.parse_args()

    main(args)