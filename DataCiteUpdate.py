import requests
import argparse
import json
import pprint
import os


def getDataCiteQuery(tier, query):
    if tier == 'test':
        url = 'https://api.test.datacite.org/'
    elif tier == 'prod':
        url = 'https://api.datacite.org/'
    else:
        print("Tier must be 'test' or 'prod' ")
        return None
    url = f"{url}{query}"
    try:
        print(url)
        results = requests.get(url)
    except requests.exceptions.HTTPError as e:
        return (f"HTTPError:\n{e}")
    if results.status_code == 200:
        results = json.loads(results.content.decode())
        return results
    else:
        return (f"Error Code: {results.status_code}\n{results.content}")



def putDataCiteQuery(tier, query):
    if tier == 'test':
        url = 'https://api.test.datacite.org/'
    elif tier == 'prod':
        url = 'https://api.datacite.org/'
    else:
        print("Tier must be 'test' or 'prod' ")
        return None
    url = f"{url}{query}"
    headers = {"Content-Type: application/vnd.api+json"}
    params = {"user": f"{os.getenv('CANANOUSER')}:{os.getenv('CANANOPASS')}"}

    try:
        print(url)
        results = requests.put(url=url, headers=headers, params=params, json=query)
    except requests.exceptions.HTTPError as e:
        return (f"HTTPError:\n{e}")
    if results.status_code == 200:
        results = json.loads(results.content.decode())
        return results
    else:
        return (f"Error Code: {results.status_code}\n{results.content}")



def main(args):
    tier = 'prod'
    doi = '10.17917/YTHD-KF51'
    #doi = '10.14454/FXWS-0523'
    results = getDataCiteQuery(tier, f"dois/{doi}")
    pprint.pprint(results)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    #parser.add_argument("-c", "--configfile", required=True,  help="Configuration file containing all the input info")
    parser.add_argument('-v', '--verbose', action='count', default=0, help=("Verbosity: -v main section -vv subroutine messages -vvv data returned shown"))

    args = parser.parse_args()

    main(args)