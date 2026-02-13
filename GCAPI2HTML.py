# Creates DOI HTML pages from info from the GC API
import pandas as pd
import numpy as np
import argparse
import yaml
import os
import sqlite3
import requests
import json
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



def readXL(xlfile, sheetlist):
    df_collection = {}
    for sheet in sheetlist:
        temp_df = pd.read_excel(xlfile, sheet_name=sheet)
        df_collection[sheet] = temp_df
    return df_collection



def writeDOIFiles(doi_df, writedir, logo, verbose=0):

    #main_df = doi_df['Protocol']
    #dbdata = []
    

    for index, row in doi_df.iterrows():
    #if row['doi'] is not np.nan:
            outfile = f"{writedir}{row['protocol_pk_id']}.html"
            if verbose >= 2:
                print(f"Writing {outfile}")
            with open(outfile, 'w') as f:
                url = f"http://dx.doi.org/{row.doi.strip()}"
                #dbdata.append((row.protocol_name, f"{row.protocol_pk_id}", 'Protocol', row.doi.strip()))
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
                #f.write("<p><b>Protocol File:</b> {}".format(row.file_name))
                #f.write("<p><b>File Title:</b> {}</p>".format(row.title))
                #f.write("<p><b>Description:</b></b> {}".format(row.description))
                f.write(separator)
                f.write("<p><b>Resource Type:</b>  Protocol</p>")
                f.write("<p><b>Data Access:</b> <a href ={}>{}</a><p>".format(gcurl, gcurl))
                f.write("</body>")
                f.write("</html>")
            f.close()
    #return dbdata



def writeIndexFile(cursor, writedir, logo, verbose=0):
    #CREATE TABLE fileinfo(doi,phs, protocol_name, protocol_pk_id, protocol_type)
    # WILL NOT WORK UNTIL THE FILE NODE IS ADDED

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
        for row in cursor.execute("SELECT protocol_name, filename, filetype, doi FROM fileinfo"):
            url = "https://cbiit.github.io/NCI-DOI-LandingPages/caNanoLab/{}".format(f"{row[1]}.html")
            r.write("<tr><td><a href={}>{}</a></td><td>{}</td></tr>".format(url, row[3], row[0]))
        r.write("</table")
        r.write("</body>")
        r.write("</html>")
        r.close()



def pullKnownFiles(df, cursor):
    # NOTE: This needs an update to work with info from the API
    known = []
    seriieslist = []
    #main_df = df['Protocol']

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

def buildDOIDataFrame():
    allquery = """
         query allProtocols(
                $phs: String!,
                $first: Int
                $offset: Int
            ){
                protocolsCount(phs_accession: $phs)
                protocols(phs_accession: $phs, first: $first, offset: $offset){
                    doi
                    phs_accession
                    protocol_name
                    protocol_pk_id
                    protocol_type
                }
            }
    """
    protocolcountquery = """
            query protocolCount($phs: String!){
                protocolsCount(phs_accession: $phs)
            }
        """

    devurl = 'https://general-dev2.datacommons.cancer.gov/v1/graphql/'
    countvars =  {"phs":"GC000001"}

    countres = runBentoAPIQuery(devurl, protocolcountquery,countvars)
    count = countres['data']['protocolsCount']

    variables = {"phs":"GC000001", "first":count, "offset": 0}
    res = runBentoAPIQuery(devurl, allquery, variables)

    doilist = []
    count = res['data']['protocolsCount']
    for entry in res['data']['protocols']:
        if '10' in entry['doi']:
            doilist.append(entry)
    doi_df = pd.DataFrame(doilist)
    return doi_df

def main(args):
    logo = '<img src="./assets/images/crdc-logo.svg" alt="CRDC General Commons Logo">'
    cursor = None

    if args.verbose >= 1:
        print("Reading configuration file")
    configs = readYAML(args.configfile)

    #Make sure there's a / at the end of the directory
    writedir = configs['writedir']
    if writedir[-1] != '/':
        writedir = writedir+'/'


    if args.verbose >- 1:
        print(f"Checking for sqlite file {writedir}{configs['sqlitefile']}")
    if os.path.isfile(f"{writedir}{configs['sqlitefile']}"):
        if args.verbose >=1:
            print("Datadase existing, establishing connection")
            conn = sqlite3.connect(f"{writedir}{configs['sqlitefile']}")
            cursor = conn.cursor()
    else:
        if args.verbose >= 1:
            print("No database found, creating a new one")
        conn = sqlite3.connect(f"{writedir}{configs['sqlitefile']}")
        cursor = conn.cursor()
        #cursor.execute("CREATE TABLE fileinfo(title, filename, filetype, doi)")
        cursor.execute("CREATE TABLE fileinfo(doi,phs, protocol_name, protocol_pk_id, protocol_type)")


    ###########################################
    #                                         #
    #                 API Queries             #
    #                                         #
    ###########################################

    '''allquery = """
            query allProtocols(
                $phs: String!,
                $first: Int
                $offset: Int
            ){
                protocolsCount(phs_accession: $phs)
                protocols(phs_accession: $phs, first: $first, offset: $offset){
                    doi
                    phs_accession
                    protocol_name
                    protocol_pk_id
                    protocol_type
                }
            }
            """
        
    protocolcountquery = """
            query protocolCount($phs: String!){
                protocolsCount(phs_accession: $phs)
            }
        """
'''
    ###########################################
    #                                         #
    #                 ALL scope               #
    #                                         #
    ###########################################

    if configs['scope'] == 'all':
        if args.verbose >= 1:
            print("Scope is all pages")
            print("Getting list of existing files")


        #devurl = 'https://general-dev2.datacommons.cancer.gov/v1/graphql/'
        #countvars =  {"phs":"GC000001"}

        #countres = runBentoAPIQuery(devurl, protocolcountquery,countvars)
        #count = countres['data']['protocolsCount']
        #print(f"Count: {count}")

        #variables = {"phs":"GC000001", "first":count, "offset": 0}
        #res = runBentoAPIQuery(devurl, allquery, variables)

        #doilist = []
        #count = res['data']['protocolsCount']
        #for entry in res['data']['protocols']:
        #    if '10' in entry['doi']:
        #        doilist.append(entry)
        #doi_df = pd.DataFrame(doilist)

        doi_df = buildDOIDataFrame()

        if args.verbose >= 1:
            print("Clearing existing database")
        cursor.execute("DELETE FROM fileinfo")

        if args.verbose >= 1:
            print("Writing individual DOI files")
        writeDOIFiles(doi_df,writedir, logo, args.verbose)

        if args.verbose >= 3:
            print(doi_df.head())
        
        if args.verbose >= 1:
            print(f"Adding info to database {configs['sqlitefile']}")
        #newlist =  [[value for value in d.values()]for d in doilist]
        newlist = []
        for index, row in doi_df.iterrows():
            temp = row.values.flatten().tolist()
            newlist.append(temp)
        cursor.executemany("INSERT INTO fileinfo VALUES(?,?,?,?,?)", newlist)
        conn.commit()

    
    ###########################################
    #                                         #
    #                 INDEX scope             #
    #                                         #
    ###########################################

    elif configs['scope'] == 'index':
        if args.verbose >= 1:
            print("Scope is index page only")
            print('Generating a new index.html file')
        writeIndexFile(cursor, writedir, logo, args.verbose)

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
        doi_df = buildDOIDataFrame()
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