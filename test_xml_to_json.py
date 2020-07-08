import json
import xmltodict




with open("./generated-data/patient-2004454.fhir-bundle.xml") as xml_file: 
      
    data_dict = xmltodict.parse(xml_file.read()) 
    xml_file.close() 
      
    # generate the object using json.dumps()  
    # corresponding to json data 
      
    json_data = json.dumps(data_dict) 
    print(json_data)
    # Write the json data to output  
    # json file 
    with open("data.json", "w") as json_file: 
        json_file.write(json_data) 
        json_file.close() 

