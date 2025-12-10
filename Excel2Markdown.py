# Reads the Excel file from ISB and creates a markdown page for each line
import pandas as pd
import numpy as np
import argparse
import yaml


def readYAML(yamlfile):
    with open(yamlfile) as f:
        yamljson = yaml.load(f, Loader=yaml.FullLoader)
    return yamljson


def writeDOIFiles(doi_df, writedir, logo):

    filenames = []

    header = "# caNanoLab DOI\n"
    separator = "--------------------------\n"
    tableheader = "| Property | Value |\n"
    tableseparator = "|----------|---------|\n"

    for index, row in doi_df.iterrows():
        outfile = f"{writedir}{row['protocol_pk_id']}.md"
        filenames.append({row['protocol_abbreviation']: f"./{row["protocol_pk_id"]}.md"})
        with open(outfile, 'w') as f:
            f.write(logo)
            f.write(header)
            f.write(separator)
            f.write(f"## DOI:\t")
            if row['doi'] is not np.nan:
                f.write(f"[{row['doi']}](http://dx.doi.org/{row['doi']})\n")
            else:
                f.write("Not Available\n")
            f.write(f"**Protocol Name:**\t")
            f.write(f"{row['protocol_name']} \\")
            f.write(f"**Protocol Abbreviation:**\t")
            f.write(f"{row['protocol_abbreviation']} \\")
            f.write(f"**Protocol Version:**\t")
            f.write(f"{row['protocol_version']} \\")
            f.write(separator)
            f.write("### Resource Type:\t")
            f.write("publication_type\n")
            f.write("### Publication Status:\t")
            f.write("publication_status\n")
            f.write(f"#### Created Date:\t")
            f.write(f"{row['created_date']}\n")
            f.write(separator)
            f.write(tableheader)
            f.write(tableseparator)
            f.write("| Sample ID | sample_id |\n")
            f.write("| Sample Name | sample_name |\n")
            f.write("| Organization | organization_name |\n")
            f.write("| Characterization ID | charid |\n")
            f.write("| Characterization Type | characterization_type |\n")
            f.write("| Assay Type | characterization_name |\n")
            f.write("| Protocol ID | protocol_id |\n")
            f.write(f"| Protocol Type | {row['protocol_type']} |\n")
            f.write(f"| Protocol Name |{row['protocol_name']} |\n")
            f.write("| Nanomaterial Entity Type | nanomaterial_entity_type |\n")
            f.write("| Composing Element Type | composing_element_type |\n")
            f.write("| Composing Element Chemical Name | composing_element_chemical_name |\n")
            f.write("| Nanomaterial Entity File Type | nanomaterial_entity_file_type |\n")
            f.write("| Chemical Association File Type Title | chemical_association_file_type_title |\n")
            f.close()
    return filenames



def writeIndexFile(filenames, writedir, logo):

    separator = "--------------------------\n"


    indexfilename = f"{writedir}index.md"
    with open(indexfilename, 'w') as r:
        r.write(logo)
        r.write("## Example Layout Pages)\n")
        r.write(separator)
        r.write("[Table Example](./demopage-table.md) \\\n")
        r.write("[Text Example](./demopage-text.md) \\\n")
        r.write("[NCI Logo](./demopage-table-NCILogo.md) \\\n")
        r.write("[caNano Logo](./demopage-table-caNanoLogo.md) \\\n")
        r.write("[General Commons Logo](./demopage-table-GCLogo.md) \\\n")
        r.write("# caNanoLab DOI Repository\n")
        r.write(separator)
        r.write("This repository contains the DOI landing pages for the caNanoLab project.\n")
        r.write("\n")
        r.write("## DOI Pages\n")
        r.write(separator)
        for entry in filenames:
            for abbreviation, url in entry.items():
                r.write(f"[{abbreviation}]({url}) \\\n")
        r.close()



def main(args):

    logo = "![General Commons Logo](./assets/images/crdc-logo.svg)\n"
    


    if args.versbose >= 1:
        print("Reading configuration file")
    configs = readYAML(args.configfile)

    if args.verbose >= 1:
        print(f"Creating datafrom from {configs['xlfile']}")
    doi_df = pd.read_excel(configs['xlfile'], sheet_name=configs['sheet'])

    if args.verbose >= 1:
        print("Writing individual DOI files")
    doi_file_list = writeDOIFiles(doi_df, configs['writedir'], logo)

    if args.verbose >=1:
        print("Writing index.md file")
    writeIndexFile(doi_file_list, configs['writedir'], logo)



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--configfile", required=True,  help="Configuration file containing all the input info")
    parser.add_argument('-v', '--verbose', action='count', default=0, help=("Verbosity: -v main section -vv subroutine messages -vvv data returned shown"))

    args = parser.parse_args()

    main(args)
