# Updates Data Cite DOI Records
# https://support.datacite.org/docs/updating-metadata-with-the-rest-api
# https://datacite.readthedocs.io/en/latest/

import datacite
import requests
import pandas as pd
import argparse
import yaml
import os

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


def dataCiteClient(doiprefix, testmode=True):
    conn = datacite.DataCiteRESTClient(
        username=os.getenv('DATACITEUSER'),
        password = os.getenv('DATACITEPASS'),
        prefix=doiprefix)
        #testmode=testmode)
    return conn


def getDOI(url, doi):
    newurl = f"{url}{doi}"
    print(newurl)
    results = requests.get(newurl, verify=False)
    return results.json()

def dataCiteRequest(url, doi, data):
    headers = {"Content-Type: application/vnd.api+json"}
    userpass = f"{os.getenv('DATACITEUSER')}:{os.getenv('DATACITEPASS')}"
    params = {'user': userpass}
    results = requests.post(f"{url}{doi}", data=data, headers=headers, params=params)


def main(args):

    if args.verbose >= 1:
        print(f"Reading config file {args.configfile}")
    configs = readYAML(args.configfile)

    full_df = readXL(configs['excelfile'], ['Protocol'])
    prot_df = full_df['Protocol']
    #prot_df.dropna(subset=['doi'])
    prot_df = prot_df[prot_df['doi'].notna()]
    print(prot_df)

    updateurl = 'https://STUFF GO HERE'
    updatejson = {
        "data": {
            "type": "dois",
            "attributes": {
                "url": updateurl
            }
        }
    }

    conn = dataCiteClient(configs['doiprefix'], True)
    for index, row in prot_df.iterrows():
        print(row['doi'])
        #conn.get_metadata(row['doi'])
        print(getDOI(configs['dataCiteUrl'], row['doi']))


    #conn = dataCiteClient(configs['doiprefix'], True)



    #metadata = conn.get_metadata(doi)
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--configfile", required=True,  help="Configuration file containing all the input info")
    parser.add_argument('-v', '--verbose', action='count', default=0, help=("Verbosity: -v main section -vv subroutine messages -vvv data returned shown"))

    args = parser.parse_args()

    main(args)