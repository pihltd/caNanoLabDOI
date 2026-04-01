---
name: canano-sample-report
description: Generates a report for one or more caNano samples and includes sample, composition, characterization, and publication information
---

# caNano Sample Report

## General Commons GraphQL API
All caNano data are stored in the CRDC General Commons, and the GraphQL endpoint URL is https://general.datacommons.cancer.gov/v1/graphql/

## Querying the General Commons GraphQL API
Queries to the General Commons GraphQL API can be done in any language that can support POST requests over https.  An example routine written in Python is shown.

```python
def runCRDCGraphQLAPIQuery(url, query, variables=None):
    """Runs a GrpahQL Query against the GraphQL endpoint specified in the URL variable
    
    :param url: URL of the GraphQL API endpoint
    :type url: URL
    :param query: A valid GraphQL query
    :type query: String
    :param variables: a JSON object containing any variables for the provided query
    :type variables: dictionary, optional
    :return: If status_code == 200, a JSON object that is the full query response
    :rtype: dictionary
    :return: If status_code != 200, a string with error code and message
    :rtype: string
    :return: If HTTP error, the requests.HTTPError object
    :rtype: request.HTTPError
    """
    
    headers = {'accept': 'application/json'}
    try:
        if variables is None:
            results = requests.post(url, headers=headers, json={'query': query})
        else:
            results = requests.post(url, headers=headers, json={'query': query, 'variables': variables})
    except requests.exceptions.HTTPError as e:
        return (f"HTTPError:\n{e}")
        
    if results.status_code == 200:
        results = json.loads(results.content.decode())
        return results
    else:
        return (f"Error Code: {results.status_code}\n{results.content}")
```

## Queries to use
### gatAllcaNanoSamples query
This query can be used to get all sample IDs and sample information by adjusting the first and offset variables.
#### Query variables
**phs_accession**: This should be set to "10.17917"
**first**: This sets the number of records to return
**offset**:  This sets the number of records to skip

For example, setting the **first** variable to 100 with **offset** set to 0 would return the first one hundred records.  Incrementing **offset** to 100 in the next query would return the second set of one hunred records. 

```graphql
query getAllcaNanoSamples(
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
}
```
*Example query variables* 
```json
{"phs_accession": "10.17917", "first": 100, "offset": 0}
```

### getSampleComposition query
This query will return the composition associated with one or more samples.
#### Query variables
**phs_accession**: This should be set to "10.17917"
**sample_id**: This should be a list of caNano sample IDs

```graphql
query getSampleComposition(
  $phs_accession: String!
  $sample_id: [String]!
){
  compositions(
    phs_accession: $phs_accession,
    sample_ids: $sample_id
  ){
    crdc_id
    Composition_ID
    Nanomaterial_Entity_Type
    Functionalizing_Entity_Inherent_Function_Type
    Functionalizing_Entity_Type
    sample_id
  }
}
```
*Example query variables* 
```json
{"phs_accession": "10.17917", "sample_id":["101318656"]}
```

### geSampleCharacterization query
This query will return the characterization information associated with one or more samples.
#### Query variables
**phs_accession**: This should be set to "10.17917"
**sample_id**: This should be a list of caNano sample IDs

```graphql
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
    sample_id
    crdc_id
  }
}
```
*Example query variables* 
```json
{"phs_accession": "10.17917", "sample_id":["101318656"]}
```

### getSamplePublication query
This query will return the publication information associated with one or more samples.
#### Query variables
**phs_accession**: This should be set to "10.17917"
**sample_id**: This should be a list of caNano sample IDs


```graphql
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
    crdc_id
    sample_id
  }
}
```
*Example query variables* 
```json
{"phs_accession": "10.17917", "sample_id":["101318656"]}
```

## Creating a report
### Step 1
The first step should be to obtain a list of caNano sample IDs either as a file, direct input, or by using the getAllcaNanoSamples query

### Step 2
For each sample ID in the starting list, the corresponding composition, characterization, and publication information should be obtained using the getSampleComposition, getSampleCharacterization, and getSamplePublication queries

### Step 3
A text report should be generated listing each sample and the composition, characterization, and publication information for that sample.  Each section should be a table.