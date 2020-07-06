from testdata import CLINICAL_NOTES_FILE
import argparse
import csv


class ClinicalNote: 
    """Create instances of Clinical Note; 
also maintains complete clinical notes lists by patient id"""

    clinicalNotes = {} # Dictionary of clinical notes lists, by patient id 

    @classmethod
    def load(cls):
      """Loads patient clinical notes"""
      
      # Loop through clinical notes and build patient clinical notes lists:
      probs = csv.reader(open(CLINICAL_NOTES_FILE,'U'),dialect='excel-tab')
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
        
        # Append clinical note to the patient's clinical notes list:
        if self.pid in  self.__class__.clinicalNotes:
          self.__class__.clinicalNotes[self.pid].append(self)
        else: self.__class__.clinicalNotes[self.pid] = [self]

    def asTabString(self):
       """Returns a tab-separated string representation of a clinical note"""
       dl = [self.pid, self.date, self.title]
       s = ""
       for v in dl:
         s += "%s\t"%v 
       return s[0:-1] # Throw away the last tab

if __name__== '__main__':

  parser = argparse.ArgumentParser(description='Test Data Clinical Notes Module')
  group = parser.add_mutually_exclusive_group()
  group.add_argument('--clinicalnotes', 
          action='store_true', help='list all clinical notes')
  group.add_argument('--pid',nargs='?', const='v',
     help='display clinical notes for a given patient id (default=2169591)')
  args = parser.parse_args()
 
  ClinicalNote.load()
  if args.pid:
    if not args.pid in ClinicalNote.clinicalNotes:
      parser.error("No results found for pid = %s"%args.pid)
    probs = ClinicalNote.clinicalNotes[args.pid]
    for prob in probs: 
      print (prob.asTabString())
    

     
