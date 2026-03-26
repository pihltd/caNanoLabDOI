# This grabs what I can get from a file GraphQL Query in GC
from crdclib import crdclib
import sqlite3
import pandas as pd
import numpy as np


def runGraphQL(url, query, vars):
    result = crdclib.runBentoAPIQuery(url=url, query=query, variables=vars)
    return result['data']['files']

sqlitefile = './pages/canano.db'

conn = sqlite3.connect(sqlitefile)
cursor = conn.cursor()

dbfileinfo = []

# title, filename, filetype, doi
#for row in cursor.execute("SELECT * FROM fileinfo"):
#    dbfileinfo.append(row[0])

#print(dbfileinfo)

xlfile = '/media/sf_VMShare/caNano/GC Data Mapping_submission_templates_12032025.xlsx'
xlsheet = 'Protocol'

xl_df = pd.read_excel(xlfile, sheet_name=xlsheet)
#print(xl_df)

filenamelist = xl_df['file_name'].tolist()

filequery = """
query caNanoFiles(
  $phs_accession: String!,
  $file_name: [String]!
){
  files(
    phs_accession: $phs_accession,
    file_names: $file_name
  ){
    file_description
    file_id
    file_mapping_level
    file_name
    file_size
    file_type
    file_url_in_cds
  }
}"""


url = "https://general.datacommons.cancer.gov/v1/graphql/"
fileinfolist = []
httplist = []

for file in filenamelist:
    print(file)
    #Need to clean up files
    if file is np.nan:
        print("None filename found")
    elif "http" in file:
        httplist.append(file)
    elif "protocols" in file:
        temp = file.split("/")
        file = temp[-1]
        vars = {"phs_accession": "10.17917", "file_name": file}
        results = runGraphQL(url=url, query=filequery, vars=vars)
        for result in results:
            fileinfolist.append(result)
    else:
        vars = {"phs_accession": "10.17917", "file_name": file}
        results = runGraphQL(url=url, query=filequery, vars=vars)
        for result in results:
            fileinfolist.append(result)
 
    #print(f"File name: {file}\n{result}")

fileinfo_df = pd.DataFrame(fileinfolist)

print(fileinfo_df)