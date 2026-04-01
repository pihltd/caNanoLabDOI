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

javascriptFetch = """
<script>
            document.getElementById('downloadLink').addEventListener('click', async function(e) {
                e.preventDefault();
                
                const originalText = this.textContent;
                const apiUrl = this.href;
                
                try {
                    // Show loading state
                    this.textContent = 'Downloading...';
                    this.style.pointerEvents = 'none';
                    
                    console.log('Fetching signed URL from:', apiUrl);
                    
                    // Fetch the signed URL from the API
                    const response = await fetch(apiUrl, {
                        method: 'GET',
                        headers: {
                            'Accept': 'application/json'
                        }
                    });
                    
                    if (!response.ok) {
                        throw new Error(`Failed to retrieve signed URL: ${response.status} ${response.statusText}`);
                    }
                    
                    const data = await response.json();
                    console.log('Received signed URL data:', data);
                    
                    if (!data.url) {
                        throw new Error('No URL found in response');
                    }
                    
                    const signedUrl = data.url;
                    
                    // Method 1: Try direct navigation (simplest, works if S3 has proper headers)
                    window.location.href = signedUrl;
                    
                    // Reset after a delay
                    setTimeout(() => {
                        this.textContent = originalText;
                        this.style.pointerEvents = 'auto';
                    }, 2000);
                    
                } catch (error) {
                    console.error('Download error:', error);
                    alert(`Error downloading file: ${error.message}\n\nPlease check the browser console for details.`);
                    this.textContent = originalText;
                    this.style.pointerEvents = 'auto';
                }
            });
        </script>
"""


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

def getFileURL(filename, url):
    vars = {"phs_accession": "10.17917", "file_name": filename}
    filequery = """
        query caNanoFiles(
        $phs_accession: String!,
        $file_name: [String]!
        ){
        files(
            phs_accession: $phs_accession,
            file_names: $file_name
        ){
            file_id
            file_url_in_cds
        }
        }"""
    
    result = runBentoAPIQuery(url=url, query=filequery, variables=vars)
    resultlist = result['data']['files']
    if len(resultlist) >= 1:
        temp = resultlist[0]['file_id']
        fileid = temp.split("/")[-1]
        return f"https://nci-crdc.datacommons.io/user/data/download/{fileid}"
        
    else:
        return None
    

def processFileName(filename):
    if filename is np.nan:
        return None
    elif filename is None:
        return None
    elif "http" in filename:
        return None
    elif "protocol" in filename:
        temp = filename.split("/")
        return temp[-1]
    else:
        return filename
    




def writeDOIFiles(doi_df, writedir, logo, graphqlurl, verbose=0):
    for index, row in doi_df.iterrows():
        if verbose >= 2:
            print(row)
        if row['doi'] is not None:
            outfile = f"{writedir}{row['protocol_pk_id']}.html"
            if verbose >= 2:
                print(f"Writing {outfile}")
            with open(outfile, 'w') as f:
                url = f"http://dx.doi.org/{row.doi.strip()}"
                # Need to grab file name and file URL to boot
                filename = processFileName(row.file_name)
                if filename is not None:
                    file_url = getFileURL(filename, graphqlurl)
                else:
                    file_url = None
                f.write(pageheader1.format(url))
                f.write(pageheader2)
                f.write("<body>")
                f.write(logo)
                f.write(header)
                f.write(separator)
                f.write("<p><b>Protocol Type:</b> {}</p>".format(row.protocol_type))
                f.write("<p><b>Protocol Name:</b> {}</p>".format(row.protocol_name))
                # TODO: Protocol abbreviation and version are lost, they're not captured in GC
                #f.write("<p><b>Protocol Abbreviation:</b> {}</p>".format(row.protocol_abbreviation))
                #f.write("<p><b>Protocol Version:</b> {}".format(row.protocol_version))
                f.write(separator)
                f.write("<p><b>DOI:</b> <a href = {}>{}</a></p>".format(url, url))
                if file_url is None:
                    f.write("<p><b>Protocol File: </b>{}</p>".format(filename))
                else:
                    f.write("<p><b>Protocol File: </b><a href = {} id=\"downloadLink\">{}</a></p>".format(file_url, filename))
                # TODO: File title is lost.  Not sure what it is anyways.
                #f.write("<p><b>File Title:</b> {}</p>".format(row.title))
                # TODO: To get descriptions back, do an update submission to GC and put the exsitng descriptions into the file_description field.
                #f.write("<p><b>Description:</b></b> {}".format(row.description))
                f.write(separator)
                f.write("<p><b>Resource Type:</b>  Protocol</p>")
                f.write("<p><b>Data Access:</b> <a href ={}>{}</a><p>".format(gcurl, gcurl))
                f.write(javascriptFetch)
                f.write("</body>")
                f.write("</html>")
            f.close()



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
        for row in cursor.execute("SELECT protocol_name, file_name, file_type, doi FROM fileinfo"):
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

    # Create a list of known files from the sqlite db
    for row in cursor.execute("SELECT file_name FROM fileinfo "):
        # Is file_id a better thing here
        known.append(row[0])
    
    # Go through the df pulled from the API and delete anything that's already in the db.
    for index, row in df.iterrows():
        if f"{row.protocol_pk_id}.html" not in known:
            seriieslist.append(row)
    new_df = pd.DataFrame(seriieslist)

    return new_df

def deleteTest(cursor, conn):
    cursor.execute("DELETE FROM fileinfo WHERE file_name LIKE '11413115%'")
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

def buildDOIDataFrame(apiurl, verbose=0):
    allquery = """
         query allProtocols(
                $phs: String!,
                $first: Int
                $offset: Int
            ){
                protocolsCount(phs_accession: $phs)
                protocols(phs_accession: $phs, first: $first, offset: $offset){
                    doi
                    file_id
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
    
    filequery = """
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
                release_datetime
            }
            }
    """

    countvars =  {"phs":"10.17917"}

    countres = runBentoAPIQuery(apiurl, protocolcountquery,countvars)
    count = countres['data']['protocolsCount']

    variables = {"phs":"10.17917", "first":count, "offset": 0}
    res = runBentoAPIQuery(apiurl, allquery, variables)

    doilist = []
    count = res['data']['protocolsCount']
    for entry in res['data']['protocols']:
        if  entry['doi'] is not np.nan:
            if entry['file_id'] is None:
                doilist.append({"doi": entry['doi'],
                            "file_id": entry['file_id'],
                            "phs_accession": entry['phs_accession'],
                            "protocol_name": entry['protocol_name'],
                            "protocol_pk_id": entry['protocol_pk_id'],
                            "protocol_type": entry['protocol_type'],
                            "file_name": None,
                            "file_type": None,
                            "file_description": None,
                            "release_datetime": None
                            })
            else:
                filevars = {"phs_accession": "10.17917", "file_ids": [entry['file_id']]}
                fileres = runBentoAPIQuery(apiurl, filequery, filevars)
                if verbose >= 3:
                    print(filevars)
                    print(fileres)
                fileinfo = fileres['data']['files'][0]
                doilist.append({"doi": entry['doi'],
                            "file_id": entry['file_id'],
                            "phs_accession": entry['phs_accession'],
                            "protocol_name": entry['protocol_name'],
                            "protocol_pk_id": entry['protocol_pk_id'],
                            "protocol_type": entry['protocol_type'],
                            "file_name": fileinfo['file_name'],
                            "file_type": fileinfo['file_type'],
                            "file_description": fileinfo['file_description'],
                            "release_datetime": fileinfo['release_datetime']
                            })
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
        cursor.execute("CREATE TABLE fileinfo(doi,file_id,phs, protocol_name, protocol_pk_id, protocol_type,file_name, file_type, file_description,release_datetime)")
    #######################################################################
        # Table columns and explanations
        # doi:  The DOI value for the file/protocol
        # file_id: The CRDC ID for the file.  The UUID portaion is used to get the signed URL from DCF
        # phs:  The phs nubmer of the project (in this case the DOI root)
        # protocol name: The protocol name.
        # protocol_pk_id.  Is used to name the html file.
        # protocol_type: The curated type of protocol provided with the submission
        # file_name: Text name of the file that can be downloaded 
        # file_type:  Hard coded to "protocol"
        # file_description: Text description of the file
        # release_datetime: The timestamp for the file release.
   


    ###########################################
    #                                         #
    #                 ALL scope               #
    #                                         #
    ###########################################

    if configs['scope'] == 'all':
        if args.verbose >= 1:
            print("Scope is all pages")
            print("Getting list of existing files")


        doi_df = buildDOIDataFrame(configs['apiurl'])

        if args.verbose >= 1:
            print("Clearing existing database")
        cursor.execute("DELETE FROM fileinfo")

        if args.verbose >= 1:
            print("Writing individual DOI files")
        writeDOIFiles(doi_df,writedir, logo, configs['apiurl'], args.verbose)

        if args.verbose >= 3:
            print(doi_df.head())
        
        if args.verbose >= 1:
            print(f"Adding info to database {configs['sqlitefile']}")
        newlist = []
        for index, row in doi_df.iterrows():
            temp = row.values.flatten().tolist()
            newlist.append(temp)
        cursor.executemany("INSERT INTO fileinfo VALUES(?,?,?,?,?,?,?,?,?,?)", newlist)
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
        #deleteTest(cursor, conn)
        #
        #      FOR TESTING ONLY
        #

        if args.verbose >= 1:
            print("Scope is new pages only")
        doi_df = buildDOIDataFrame(configs['apiurl'])
        if args.verbose >= 1:
            print("Removing existing files")
        doi_df = pullKnownFiles(doi_df, cursor)
        if args.verbose >= 1:
            print("Writing new DOI files")
        writeDOIFiles(doi_df=doi_df, writedir=writedir, logo=logo, graphqlurl=configs['apiurl'], verbose=args.verbose)
        if args.verbose >= 1:
            print(f"Updating database {configs['sqlitefile']} with new files")
        if args.verbose >= 2:
            print(f"Data Update:\n{doi_df}")
        newlist = []
        for index, row in doi_df.iterrows():
            temp = row.values.flatten().tolist()
            newlist.append(temp)
        cursor.executemany("INSERT INTO fileinfo VALUES(?,?,?,?,?,?,?,?,?,?)", newlist)
        conn.commit()
        if args.verbose >= 1:
            print("Writing new index.html file")
        writeIndexFile(cursor, configs['writedir'], logo, args.verbose)

    else:
        print('Incorrect scope setting, must be one of "all", "new", or "index"')





if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--configfile", required=True,  help="Configuration file containing all the input info")
    parser.add_argument('-v', '--verbose', action='count', default=0, help=("Verbosity: -v main section -vv subroutine messages -vvv data returned shown"))

    args = parser.parse_args()

    main(args)