import pandas as pd
import yaml
from crdclib import crdclib
from tqdm import tqdm

def getSampleInfo(url):

    #TODO: Revist retunred info after GC fixes the API bug. Sample Name does not appear to be in the schema but the data may be in sample description
    sampleQuery = """
    query getAllCaNanoSamples(
        $phs_accession: String!,
        $first: Int,
        $offset: Int
    ){
    samples(
        phs_accession: $phs_accession,
        first: $first,
        offset: $offset
    ){
        sample_id
        sample_description
        Organization_Name
        sample_type
        }
    }"""

    first = 100
    offset = 0
    finalSampleList = []
    while offset >= 0:
        sampleVars = {"phs_accession": "10.17917", "first": first, "offset": offset}
        sampleinfo = crdclib.runBentoAPIQuery(url=url, query=sampleQuery, variables=sampleVars)
        sampleList = sampleinfo['data']['samples']
        if len(sampleList) == 100:
            offset = offset+100
        else:
            offset = -1
        for entry in sampleList:
            finalSampleList.append(entry)
    return finalSampleList
        


def getCompositionInfo(sampleID, url):

    compositionQuery = """
        query getSampleComposition(
            $phs_accession: String!
            $sample_id: [String]!
            ){
        compositions(
            phs_accession: $phs_accession,
            sample_ids: $sample_id
            ){
                Composition_ID
                Nanomaterial_Entity_Type
                Functionalizing_Entity_Inherent_Function_Type
                Functionalizing_Entity_Type
            }
        }
    """

    compVars = {"phs_accession": "10.17917", "sample_id": [sampleID]}

    compDictionary = crdclib.runBentoAPIQuery(url=url, query=compositionQuery, variables=compVars)
    return compDictionary['data']['compositions']


def getCharacterizationInfo(sampleID, url):
    characterizationQuery = """
        query getSampleCharacterization(
            $phs_accession: String!,
            $sample_id: [String]!
            ){
        characterizations(
            phs_accession: $phs_accession,
            sample_ids: $sample_id
            ){
                Characterization_ID
                Characterization_Name
                Characterization_Assay_Type
            }
        }
    """
    charVars = {"phs_accession": "10.17917", "sample_id": [sampleID]}

    charDictionary = crdclib.runBentoAPIQuery(url=url, query=characterizationQuery, variables=charVars)
    return charDictionary['data']['characterizations']


def getPublicationInfo(sampleID, url):
    publicationQuery = """
        query getSamplePublication(
            $phs_accession: String!,
            $sample_id: [String]!
            ){
    publications(
        phs_accession: $phs_accession,
        sample_ids: $sample_id
        ){
            DOI_or_Pub_ID
            Publication_Type
            Publication_Status
            Publication_Title
        }
    }
    """
    pubVars = {"phs_accession": "10.17917", "sample_id": [sampleID]}

    pubDictionary = crdclib.runBentoAPIQuery(url=url, query=publicationQuery, variables=pubVars)
    return pubDictionary['data']['publications']


def buildReportDictionary(sample, complist, charlist, publist):
    final = {}

    #Sample Handling
    final['Sample'] = sample

    # Composition Handling
    final['Composition'] = complist

    # Characterization handling
    final['Characterization'] = charlist

    # Publication handling
    final['Publication'] = publist

    return final



def writeYAML(filename, jsonobj):
    with open(filename, 'w') as f:
        yaml.dump(jsonobj, f, sort_keys=False)
    f.close()


#
# Temporary:  Read sample information from a csv
#

# samplelist = getSampleInfo(graphqlurl)

samplefile = '/media/sf_VMShare/caNano/GC_sample_Download 2026-04-01 08-33-07.csv'
sample_df = pd.read_csv(samplefile, sep=",")
graphqlurl = 'https://general.datacommons.cancer.gov/v1/graphql/'
reportDir = "./sampleReports/"
progress_bar = tqdm(total=len(sample_df))

for index, row in sample_df.iterrows():
    complist = getCompositionInfo(row['Sample ID'], graphqlurl)
    charlist = getCharacterizationInfo(row['Sample ID'], graphqlurl)
    publist = getPublicationInfo(row['Sample ID'], graphqlurl)
    reportFileName = f"{reportDir}{row['Sample ID']}_Sample_Report_API.yml"
    # Temp until API works:
    sampledict = {"sample_id": row['Sample ID'],
                  "Sample_Name": row['Sample Name'],
                  "Organization_Name": row['Organization Name']}
    

    reportDicttionary = buildReportDictionary(sample=sampledict, complist=complist, charlist=charlist, publist=publist)

    writeYAML(reportFileName, reportDicttionary)
    progress_bar.update(1)
    
