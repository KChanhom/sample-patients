from testdata import DOCUMENTS_FILE
import argparse
import csv


class Document: 
    """Create instances of Document; 
also maintains complete documents lists by patient id"""

    documents = {} # Dictionary of documents lists, by patient id 

    @classmethod
    def load(cls):
      """Loads patient documents"""
      
      # Loop through documents and build patient documents lists:
      probs = csv.reader(open(DOCUMENTS_FILE,'U'),dialect='excel-tab')
      # header = probs.next() 
      header = next(probs)

      for prob in probs:
          cls(dict(zip(header,prob))) # Create a clinical note instance 

    def __init__(self,p):
        self.id = p['ID']
        self.pid = p['PID']
        self.date = p['DATE']
        self.title = p['TITLE']
        self.mime_type = p['MIME_TYPE']
        self.file_name = p['FILE_NAME']
        self.type = p['TYPE']
        
        # Append document to the patient's documents list:
        if self.pid in  self.__class__.documents:
          self.__class__.documents[self.pid].append(self)
        else: self.__class__.documents[self.pid] = [self]

    def asTabString(self):
       """Returns a tab-separated string representation of a document"""
       dl = [self.pid, self.date, self.title]
       s = ""
       for v in dl:
         s += "%s\t"%v 
       return s[0:-1] # Throw away the last tab

if __name__== '__main__':

  parser = argparse.ArgumentParser(description='Test Data Documents Module')
  group = parser.add_mutually_exclusive_group()
  group.add_argument('--documents', 
          action='store_true', help='list all documents')
  group.add_argument('--pid',nargs='?', const='v',
     help='display documents for a given patient id (default=2169591)')
  args = parser.parse_args()
 
  Document.load()
  if args.pid:
    if not args.pid in Document.documents:
      parser.error("No results found for pid = %s"%args.pid)
    probs = Document.documents[args.pid]
    for prob in probs: 
      print (prob.asTabString())
    

     
