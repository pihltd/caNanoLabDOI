# Reads the Excel file from ISB and creates an HTML page for each line
# https://dcf.gen3.org/data-access-with-dcf
import pandas as pd
import numpy as np
import argparse
import yaml
import os
import sqlite3
import requests
import json


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

def getFileURL(filename):
    url = "https://general.datacommons.cancer.gov/v1/graphql/"
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
    #print(f"Filename: {filename}\nResult: {result}\n")
    resultlist = result['data']['files']
    if len(resultlist) >= 1:
        #return resultlist[0]['file_id'].split("/")[-1]
        temp = resultlist[0]['file_id']
        fileid = temp.split("/")[-1]
        return f"https://nci-crdc.datacommons.io/user/data/download/{fileid}"
        
    else:
        return None

def processFileName(filename):
    if filename is np.nan:
        return None
    elif "http" in filename:
        return None
    elif "protocol" in filename:
        temp = filename.split("/")
        return temp[-1]
    else:
        return filename


def writeDOIFiles(doi_df, writedir, logo):
    # TODO: If protocol file name is None, don't add a link

    main_df = doi_df['Protocol']
    dbdata = []

    for index, row in main_df.iterrows():
        if row['doi'] is not np.nan:
            outfile = f"{writedir}{row['protocol_pk_id']}.html"
            with open(outfile, 'w') as f:
                url = f"http://dx.doi.org/{row.doi.strip()}"
                # Need to grab file name and file URL to boot
                filename = processFileName(row.file_name)
                if filename is not None:
                    file_url = getFileURL(filename)
                else:
                    file_url = None
                dbdata.append((row.protocol_name, f"{row.protocol_pk_id}", 'Protocol', row.doi.strip(), filename, file_url))
                f.write(pageheader1.format(url))
                f.write(pageheader2)
                f.write("<body>")
                f.write(logo)
                f.write(header)
                f.write(separator)
                f.write("<p><b>Protocol Type:</b> {}</p>".format(row.protocol_type))
                f.write("<p><b>Protocol Name:</b> {}</p>".format(row.protocol_name))
                f.write("<p><b>Protocol Abbreviation:</b> {}</p>".format(row.protocol_abbreviation))
                f.write("<p><b>Protocol Version:</b> {}".format(row.protocol_version))
                f.write(separator)
                f.write("<p><b>DOI:</b> <a href = {}>{}</a></p>".format(url, url))
                if file_url is None:
                    f.write("<p><b>Protocol File: </b>{}</p>".format(filename))
                else:
                    f.write("<p><b>Protocol File: </b><a href = {} id=\"downloadLink\">{}</a></p>".format(file_url, filename))
                f.write("<p><b>File Title:</b> {}</p>".format(row.title))
                f.write("<p><b>Description:</b></b> {}".format(row.description))
                f.write(separator)
                f.write("<p><b>Resource Type:</b>  Protocol</p>")
                f.write("<p><b>Data Access:</b> <a href ={}>{}</a><p>".format(gcurl, gcurl))
                f.write(javascriptFetch)
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
        for row in cursor.execute("SELECT protocol_name, protocol_pk_id, filetype, doi FROM fileinfo"):
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

    for row in cursor.execute("SELECT protocol_pk_id FROM fileinfo "):
        known.append(row[0])
    for index, row in main_df.iterrows():
        if f"{row.protocol_pk_id}.md" not in known:
            seriieslist.append(row)
    new_df = pd.DataFrame(seriieslist)
    df['Protocol'] = new_df
    return df

def deleteTest(cursor, conn):
    cursor.execute("DELETE FROM fileinfo WHERE protocol_pk_id LIKE '11413115%'")
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
        #######################################################################
        # Table columns and explanations
        # title: The protocol name.  RENAME TO protocol_name
        # filename The protocol_pk_id.  Is used to name the html file.  RENAME TO protocol_pk_id
        # filetype:  Hard coded to "protocol"
        # doi: The doi for the entry
        # protocol_file: The downloadable protocol file
        # protocol_url:  The URL allowing download of the protocol file.
        #cursor.execute("CREATE TABLE fileinfo(title, filename, filetype, doi)")
        cursor.execute("CREATE TABLE fileinfo(protocol_name, protocol_pk_id, filetype, doi, protocol_file, protocol_url)")
        
    ###########################################
    #                                         #
    #                 ALL scope               #
    #                                         #
    ###########################################

    if configs['scope'] == 'all':
        if args.verbose >= 1:
            print("Scope is all pages")
            print("Getting list of existing files")
        if args.verbose >= 1:
            print(f"Creating datafrom from {configs['xlfile']}")
        doi_df = readXL(configs['xlfile'], configs['sheet'])
        if args.verbose >= 1:
            print("Clearing existing database")
        cursor.execute("DELETE FROM fileinfo")
        if args.verbose >= 1:
            print("Writing individual DOI files")
        dbdata = writeDOIFiles(doi_df, configs['writedir'], logo)
        if args.verbose >= 1:
            print(f"Adding info to database {configs['sqlitefile']}")
        cursor.executemany("INSERT INTO fileinfo VALUES(?,?,?,?,?,?)", dbdata)
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
        doi_df = readXL(configs['xlfile'], configs['sheet'])
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
        cursor.executemany("INSERT INTO fileinfo VALUES(?,?,?,?,?,?)", dbdata)
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