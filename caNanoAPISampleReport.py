import pandas as pd
import yaml
from crdclib import crdclib
from rich.progress import Progress

def getSampleInfo(url):

    countQuery = """
        query getSamplesCount(
        $phs_accession: String!){
        samplesCount(phs_accession:$phs_accession)}
    """
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

    #Get the total sample count
    samplecountjson = crdclib.runBentoAPIQuery(url=url, query=countQuery, variables={"phs_accession":"10.17917"})
    samplecount = int(samplecountjson['data']['samplesCount'])


    first = 100
    offset = 0
    finalSampleList = []
    with Progress() as p:
        t=p.add_task("Collecting Initial Sample Info....", total=samplecount)
        while offset >= 0:
            sampleVars = {"phs_accession": "10.17917", "first": first, "offset": offset}
            sampleinfo = crdclib.runBentoAPIQuery(url=url, query=sampleQuery, variables=sampleVars)
            sampleList = sampleinfo['data']['samples']
            # If the sampleList is less than first, it means it's the last set of results and the loop should end
            if len(sampleList) == first:
                offset = offset+first
            else:
                offset = -1
            for entry in sampleList:
                finalSampleList.append(entry)
            p.update(t, advance=first)
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


def listify(startstring):
    startstring = startstring.replace("[","")
    startstring = startstring.replace("]","")
    startstring = startstring.replace("' ", "")
    startstring = startstring.replace("'", "")
    startstring = startstring.replace('"',"")
    startlist = startstring.split(",")
    newlist = []
    for entry in startlist:
        entry = entry.strip()
        newlist.append(crdclib.cleanString(entry, True))
    return newlist


def buildReportDictionary(sample, complist, charlist, publist):
    final = {}
    newcomplist = []
    newcharlist = []

    for entry in complist:
        netlist = listify(entry['Nanomaterial_Entity_Type'])
        feiftlist = listify(entry['Functionalizing_Entity_Inherent_Function_Type'])
        fetlist = listify(entry['Functionalizing_Entity_Type'])
        newcomplist.append({"Composition_ID":entry['Composition_ID'],
                           'Nanomaterial_Entity_Type': netlist,
                            'Functionalizing_Entity_Inherent_Function_Type': feiftlist,
                             'Functionalizing_Entity_Type': fetlist })
        
    for entry in charlist:
        charnamelist = listify(entry['Characterization_Name'])
        newcharlist.append({'Characterization_ID': entry['Characterization_ID'],
                            'Characterization_Name': charnamelist,
                            'Characterization_Assay_Type': entry['Characterization_Assay_Type']})



    #Sample Handling
    final['Sample'] = sample

    # Composition Handling
    final['Composition'] = newcomplist

    # Characterization handling
    final['Characterization'] = newcharlist

    # Publication handling
    final['Publication'] = publist

    return final



def writeYAML(filename, jsonobj):
    with open(filename, 'w') as f:
        yaml.dump(jsonobj, f, sort_keys=False)
    f.close()


graphqlurl = 'https://general-dev2.datacommons.cancer.gov/v1/graphql/'

samplelist = getSampleInfo(graphqlurl)
sample_df = pd.DataFrame(samplelist)

#samplefile = '/media/sf_VMShare/caNano/GC_sample_Download 2026-04-01 08-33-07.csv'
#sample_df = pd.read_csv(samplefile, sep=",")

reportDir = "./sampleReports/"
with Progress() as p:
    t = p.add_task("Creating Sample reports.....", total=len(sample_df))

    for index, row in sample_df.iterrows():
        #complist = getCompositionInfo(row['Sample ID'], graphqlurl)
        complist = getCompositionInfo(row['sample_id'], graphqlurl)
        #charlist = getCharacterizationInfo(row['Sample ID'], graphqlurl)
        charlist = getCharacterizationInfo(row['sample_id'], graphqlurl)
        #publist = getPublicationInfo(row['Sample ID'], graphqlurl)
        publist = getPublicationInfo(row['sample_id'], graphqlurl)
        #reportFileName = f"{reportDir}{row['Sample ID']}_Sample_Report_API.yml"
        reportFileName = f"{reportDir}{row['sample_id']}_Sample_Report_API.yml"
        # Temp until API works:
        #sampledict = {"sample_id": row['Sample ID'],
        #            "Sample_Name": row['Sample Name'],
        #            "Organization_Name": row['Organization Name']}
        sampledict = {"sample_id": row['sample_id'],
                    "Sample_Description": row['sample_description'],
                    "Organization_Name": row['Organization_Name'],
                    "Sample_Type": row['sample_type']}
        

        reportDicttionary = buildReportDictionary(sample=sampledict, complist=complist, charlist=charlist, publist=publist)

        writeYAML(reportFileName, reportDicttionary)
        p.update(t, advance=1)
    
