# Checks to see if a file UUID returns a signed URL from DCF or doesthe 404 thing.
import requests
import pandas as pd
import numpy as np
from crdclib import crdclib
import requests
import json


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
    
    result = crdclib.runBentoAPIQuery(url=url, query=filequery, variables=vars)
    resultlist = result['data']['files']
    if len(resultlist) >= 1:
        temp = resultlist[0]['file_id']
        fileid = temp.split("/")[-1]
        return f"https://nci-crdc.datacommons.io/user/data/download/{fileid}"
        
    else:
        return None
    

def runDCFQuery(url):
    if url is None:
        return None
    else:
        try:
            results = requests.get(url)
        except requests.exceptions.HTTPError as e:
            return (f"HTTPError:\n{e}")
        if results.status_code == '200':
            results = json.loads(results.content.decode())
            return results['url']
        else:
            return results.status_code
    

xlfile = '/media/sf_VMShare/caNano/GC Data Mapping_submission_templates_12032025.xlsx'

prot_df = pd.read_excel(xlfile, 'Protocol')

info = []

for index, row in prot_df.iterrows():
    if row['doi'] is not np.nan:
        filename = processFileName(row['file_name'])
        print(f"Working on {filename}")
        if filename is not None:
            fileurl = getFileURL(filename=filename)
            dcfinfo = runDCFQuery(fileurl)

            info.append({'file_name': filename, 'fetch_url': fileurl, 'dcf_status': dcfinfo})

report_df = pd.DataFrame(info)

reportfile = '/media/sf_VMShare/caNano/dcf_report.csv'
report_df.to_csv(reportfile, sep="\t", index=False)