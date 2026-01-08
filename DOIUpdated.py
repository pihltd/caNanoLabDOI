# Updates Data Cite DOI Records
# https://support.datacite.org/docs/updating-metadata-with-the-rest-api
# https://datacite.readthedocs.io/en/latest/

import requests
from requests.auth import HTTPBasicAuth
import pandas as pd
import argparse
import yaml
import os
import json
import pprint

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



def getDOI(url, doi):
    newurl = f"{url}{doi}"
    print(newurl)
    results = requests.get(newurl, verify=False)
    return results.json()

def dataCiteDryRun(doi_prefix, doi_suffix, payload, tier, loghandle):
    if tier == 'test':
        USER = os.getenv('DOITESTUSER')
        PASSWORD = os.getenv('DOITESTPASS')
        server = os.getenv('DOITESTSERVER')
    elif tier == 'prod':
        USER = os.getenv('DOIPRODUSER')
        PASSWORD = os.getenv('DOIPRODPASS')
        server = os.getenv('DOIPRODSERVER')
    else:
        return "Incorrect Tier provided, please use 'test' or 'prod'"
    pprint.pprint(f"https://{server}/dois/{doi_prefix}/{doi_suffix}")
    pprint.pprint(payload)
    loghandle.write(f"URL:\thttps://{server}/dois/{doi_prefix}/{doi_suffix}\nPayload:\t{payload}\n")
    

def dataCiteRequest(doi_prefix, doi_suffix, payload, tier, loghandle):
    if tier == 'test':
        USER = os.getenv('DOITESTUSER')
        PASSWORD = os.getenv('DOITESTPASS')
        server = os.getenv('DOITESTSERVER')
    elif tier == 'prod':
        USER = os.getenv('DOIPRODUSER')
        PASSWORD = os.getenv('DOIPRODPASS')
        server = os.getenv('DOIPRODSERVER')
    else:
        return "Incorrect Tier provided, please use 'test' or 'prod'"
    try:
        headers = {"accept": "application/vnd.api+json"}
        # From Bill's script
        url = f"https://{server}/dois/{doi_prefix}/{doi_suffix}"
        response = requests.put(url, auth=HTTPBasicAuth(USER, PASSWORD), headers=headers, json=payload)
        if response.status_code == 200:
            parsed = json.loads(response.text)
            loghandle.write(f"URL:\t{url}\n{parsed}\n")
        else:
            loghandle.write(f"URL:\t{url}\nSTATUS CODE ERROR: {response.status_code}\t {response.content}\n")
    except requests.exceptions.HTTPError as e:
        loghandle.write(f"URL:\t{url}\nHTTP ERROR: {e}\n")


def main(args):

    if args.verbose >= 1:
        print(f"Reading config file {args.configfile}")
    configs = readYAML(args.configfile)

    if args.verbose >= 1:
        print(f"Reading Excel file {configs['excelfile']}")
    full_df = readXL(configs['excelfile'], ['Protocol'])
    prot_df = full_df['Protocol']
    if args.verbose >= 1:
        print("Removing lines with no DOI")
    prot_df = prot_df[prot_df['doi'].notna()]
    if args.verbose >= 1:
        print(f"Opening log file {configs['logfile']}")
    lf = open(configs['logfile'], "w")
    if configs['testrun']:
        if args.verbose >= 1:
            print("Performing Test run on limited dataset")
        fakedoilist = []
        fakedoilist.append({'doi':'10.24368/mxby-kv24', 'protocol_pk_id': '88834070'})
        fakedoilist.append({'doi':'10.24368/wc0p-tc65', 'protocol_pk_id': '88834071'})
        fakedoilist.append({'doi':'10.24368/ac5g-ab22', 'protocol_pk_id': '88834069'})
        prot_df = pd.DataFrame(fakedoilist)

    if args.verbose >= 1:
        print(f"Starting update on {configs['tier']}")   
    for index, row in prot_df.iterrows():
        doi = row.doi.strip()
        if args.verbose >= 2:
            print(f"Updating DOI {doi}")
        doilist = doi.split('/')
        doiprefix = doilist[0]
        doisuffix = doilist[-1]
        pkid = str(row.protocol_pk_id).strip()
        if configs['testrun']:
            newdoiurl = f"https://test.cbiit.github.io/NCI-DOI-LandingPages/caNanoLab/{pkid}.html"
        else:
            newdoiurl = f"https://cbiit.github.io/NCI-DOI-LandingPages/caNanoLab/{pkid}.html"
        updatejson = {
            "data": {
                "type": "dois",
                "attributes": {
                    "url": newdoiurl
                }
            }
        }

        dataCiteRequest(doi_prefix=doiprefix, doi_suffix=doisuffix,payload=updatejson,tier='test', loghandle=lf)
        #dataCiteDryRun(doi_prefix=doiprefix, doi_suffix=doisuffix, payload=updatejson, tier=configs['tier'], loghandle=lf)
    lf.close()

       

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--configfile", required=True,  help="Configuration file containing all the input info")
    parser.add_argument('-v', '--verbose', action='count', default=0, help=("Verbosity: -v main section -vv subroutine messages -vvv data returned shown"))

    args = parser.parse_args()

    main(args)