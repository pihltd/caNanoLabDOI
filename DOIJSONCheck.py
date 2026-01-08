from bs4 import BeautifulSoup
import json
import requests
import pandas as pd

jsonfile = '/media/sf_VMShare/caNano/doiUpdate.json'
errorlist = []
fulllist = []

with open(jsonfile, "r") as f:
    doijson = json.load(f)

for entry in doijson['data']:
    newurl = entry['attributes']['url']
    doi = entry['id']
    doi=doi.strip()
    doihtml = requests.get(newurl)
    soup = BeautifulSoup(doihtml.text, 'html.parser')
    for a in soup.find_all('a', href=True):
        if 'dx.doi.org' in a['href']:
            templist = a['href'].split('/')
            newdoi = f"{templist[-2]}/{templist[-1]}"
            fulllist.append({'originalDOI': doi, 'newDOI': newdoi, 'originalLenght':len(doi), 'newLength':len(newdoi), 'newurl': newurl})
            if newdoi != doi:
                errorlist.append({'originalDOI': doi, 'newDOI': newdoi, 'originalLenght':len(doi), 'newLength':len(newdoi), 'newurl': newurl})

error_df = pd.DataFrame(errorlist)
full_df = pd.DataFrame(fulllist)

full_df.to_csv('/media/sf_VMShare/caNano/migrationReport.csv', sep="\t", index=False)
error_df.to_csv('/media/sf_VMShare/caNano/migrationErrorReport.csv', sep="\t", index=False)