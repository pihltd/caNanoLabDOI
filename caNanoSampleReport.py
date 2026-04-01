import pandas as pd
import numpy as np
from crdclib import crdclib

def parseDF(df, columns):
    temp = {}
    for column in columns:
        for index, row in df.iterrows():
            temp[column] = row[column]
    return temp

def parsePipe(property, section_dict):
    templist = section_dict[property].split("|")
    section_dict[property] = templist
    return section_dict


def revisedYamlReport(sample_df, comp_df, char_df, pub_df, sample_id, dir):
    report = {}
    sample_dict = parseDF(sample_df, sample_df.columns.tolist())
    report['Sample'] = sample_dict
    comp_dict = parseDF(comp_df, comp_df.columns.tolist())
    report['Composition'] = comp_dict
    char_dict = parseDF(char_df, char_df.columns.tolist())
    final_char=[]
    if len(char_dict) > 0:
        assay_list = str(char_dict['assay_type']).split("|")
        id_list = str(char_dict['characterization_id']).split("|")
        name_list = str(char_dict['characterization_name']).split("|")
        type_list = str(char_dict['characterization_type']).split("|")
        counter = 0
        while counter < len(id_list):
            final_char.append({"assay_type":assay_list[counter],
                               "characterization_id": id_list[counter],
                               "characterization_name": name_list[counter],
                               "characterization_type": type_list[counter]})
            counter = counter + 1

    report['Characterization'] = final_char
    pub_dict = parseDF(pub_df, pub_df.columns.tolist())
    report['Publications'] = pub_dict

    filename = f"{dir}{sample_id}_REVISEDsampleReport.yml"
    crdclib.writeYAML(filename=filename, jsonobj=report)




def yamlReport(sample_df, comp_df, char_df, pub_df, sample_id, dir):
    report = {}
    sample_dict = parseDF(sample_df, sample_df.columns.tolist())
    report['Sample'] = sample_dict
    comp_dict = parseDF(comp_df, comp_df.columns.tolist())
    report['Composition'] = comp_dict
    char_dict = parseDF(char_df, char_df.columns.tolist())
    if len(char_dict) > 0:
        fields = ['assay_type', 'characterization_id', 'characterization_name', 'characterization_type']
        for field in fields:
            if "|" in str(char_dict[field]):
                char_dict = parsePipe(field, char_dict)
    report['Characterization'] = char_dict
    pub_dict = parseDF(pub_df, pub_df.columns.tolist())
    report['Publications'] = pub_dict

    filename = f"{dir}{sample_id}_sampleReport.yml"
    crdclib.writeYAML(filename=filename, jsonobj=report)



def textReport(sample_df, comp_df, char_df, pub_df, sample_id, dir):
    filename = f"{dir}{sample_id}_sampleReport.txt"
    with open(filename, "w") as s:
        sample_dict = parseDF(sample_df, sample_df.columns.to_list())
        s.write("Sample Info\n")
        for key, value in sample_dict.items():
            s.write(f"{key}: {value}\n")
        comp_dict = parseDF(comp_df, comp_df.columns.tolist())
        s.write("\nComposition Info\n")
        for key, value in comp_dict.items():
            s.write(f"{key}: {value}\n")
        char_dict = parseDF(char_df, char_df.columns.tolist())
        s.write("\nCharacterization Info\n")
        for key, value in char_dict.items():
            s.write(f"{key}: {value}\n")
        pub_dict = parseDF(pub_df, pub_df.columns.tolist())
        s.write("\nPublication Info\n")
        for key, value in pub_dict.items():
            s.write(f"{key}: {value}\n")
    s.close()

def markdownReport(sample_df, comp_df, char_df, pub_df, sample_id, dir):
    filename = f"{dir}{sample_id}_sampleReport.md"
    with open(filename, "w") as s:
        sample_dict = parseDF(sample_df, sample_df.columns.to_list())
        s.write("**Sample Info**\n")
        for key, value in sample_dict.items():
            s.write(f"- **{key}**: {value}\n")
        comp_dict = parseDF(comp_df, comp_df.columns.tolist())
        s.write("\n**Composition Info**\n")
        for key, value in comp_dict.items():
            s.write(f"- **{key}**: {value}\n")
        char_dict = parseDF(char_df, char_df.columns.tolist())
        s.write("\nCharacterization Info\n")
        s.write("| Characterization ID | Assay Type | Characterization Name | Characterization Type |\n")
        s.write("|---------------------|------------|-----------------------|-----------------------|\n")
        if len(char_dict) > 0:
            assay_list = str(char_dict['assay_type']).split("|")
            id_list = str(char_dict['characterization_id']).split("|")
            name_list = str(char_dict['characterization_name']).split("|")
            type_list = str(char_dict['characterization_type']).split("|")
            counter = 0
            while counter < len(id_list):
                s.write(f"| {id_list[counter]} | {assay_list[counter]} | {name_list[counter]} | {type_list[counter]} |\n")
                counter = counter + 1
        pub_dict = parseDF(pub_df, pub_df.columns.tolist())
        s.write("\n**Publication Info**\n")
        for key, value in pub_dict.items():
            s.write(f"- **{key}**: {value}\n")
    s.close()
        

        


# TODO:  Once the caNano sample ID bug is fixed, this part has to be re-done to that info comes from the API, not the Excel workbook.


startingxlfile = '/media/sf_VMShare/caNano/GC Data Mapping_submission_templates_12032025.xlsx'
reportDir = "./sampleReports/"

full_sample_df = pd.read_excel(startingxlfile, 'Sample Node')
full_comp_df = pd.read_excel(startingxlfile, 'Composition')
full_char_df = pd.read_excel(startingxlfile, 'Characterization ')
full_pub_df = pd.read_excel(startingxlfile, 'Publication')

sampleList = full_sample_df['sample_id'].unique().tolist()

for sample in sampleList:
    temp_sample_df = full_sample_df.query('sample_id == @sample')
    temp_comp_df = full_comp_df.query("parentSampleID == @sample")
    temp_char_df = full_char_df.query("parentSampleID ==@sample")
    temp_pub_df = full_pub_df.query("parentSampleID == @sample")

    #yamlReport(temp_sample_df, temp_comp_df, temp_char_df, temp_pub_df, sample, reportDir )
    #textReport(temp_sample_df, temp_comp_df, temp_char_df, temp_pub_df, sample, reportDir )
    revisedYamlReport(temp_sample_df, temp_comp_df, temp_char_df, temp_pub_df, sample, reportDir )
    markdownReport(temp_sample_df, temp_comp_df, temp_char_df, temp_pub_df, sample, reportDir )

