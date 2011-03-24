"""
Example SMArt REST Application: 

 * Required "admin" app privileges on smart container
 * Pushes data into the container using "Stage 1 Write API"

Josh Mandel
Children's Hospital Boston, 2011
"""

from pipeline_base import *

def run_query(args):


    client = get_smart_client()

    sparql = """PREFIX  rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX  foaf:  <http://xmlns.com/foaf/0.1/>
PREFIX  sp:  <http://smartplatforms.org/terms#>
CONSTRUCT {?person rdf:type foaf:Person} 
WHERE   {
?person rdf:type foaf:Person. 
$statements_here
}
order by ?ln"""

    statements = []
    if args.gn:
        statements.append("?person foaf:givenName '%s'"%args.gn)
    if args.fn:
        statements.append("?person foaf:familyName '%s'"%args.fn)
    if args.zip:
        statements.append("?person sp:zipcode '%s'"%args.zip)
    if args.gender:
        statements.append("?person foaf:gender '%s'"%args.gender)
    if args.bday:
        statements.append("?person sp:birthday '%s'"%args.bday)
    if args.externalID:
        statements.append("?person sp:externalID <%s>"%args.externalID)
        

    q = sparql.replace("$statements_here", ". \n".join(statements))
    print q
    response = client.get("/records/search", data={'sparql':q})
    print response

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Query SMART Patients')

    parser.add_argument('--family-name',dest='fn', nargs='?', required=False,
                        help="Family name")

    parser.add_argument('--given-name',dest='gn', nargs='?', required=False,
                        help="Given name")

    parser.add_argument('--zip-code',dest='zip', nargs='?', required=False,
                        help="zip code")

    parser.add_argument('--birthday',dest='bday', nargs='?', required=False,
                        help="birthday as ISO-8601")

    parser.add_argument('--gender',dest='gender', nargs='?', required=False,
                        choices=['male','female'],
                        help="Gender")

    parser.add_argument('--external-uri', dest='externalID', nargs='?', 
                        help="external URI for the patient")

    args = parser.parse_args()

    run_query(args)
    

