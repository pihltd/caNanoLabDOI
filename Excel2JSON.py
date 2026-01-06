# Generates the JSON file needed to update the DOI URL records
#
#  This may not work.  According to https://support.datacite.org/docs/is-it-possible-to-update-the-url-landing-pages-of-dois
# Each update needs to be a separate PUT call
#

# "data": {
#   "id": "10.7282/t37zhk-y459",
#   "type": "dois",
#   "attributes": {
#       "url": "https://example.org"
#   }
# }

import json
import pandas as pd
import numpy as np

xlfile = r'/media/sf_VMShare/caNano/GC Data Mapping_submission_templates_12032025.xlsx'
sheet = 'Protocol'

baseurl = "https://cbiit.github.io/NCI-DOI-LandingPages/caNanoLab/{}.html"

jsonfile = '/media/sf_VMShare/caNano/doiUpdate.json'

finaljson = {}
doilist = []

doi_df = pd.read_excel(xlfile, sheet_name=sheet)

for index, row in doi_df.iterrows():
    if row['doi'] is not np.nan:
        temp = {}
        temp['type'] = 'dois'
        temp['id'] = row['doi']
        temp['attributes'] = {'url': baseurl.format(row['protocol_pk_id'])}
        doilist.append(temp)
finaljson['data'] = doilist

with open(jsonfile, "w") as f:
    json.dump(finaljson, f, indent=4)
        