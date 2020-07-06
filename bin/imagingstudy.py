from testdata import IMAGINGSTUDIES_FILE
import argparse
import csv


class ImagingStudy: 
    """Create instances of ImagingStudy; 
also maintains complete imaging studies lists by patient id"""

    imagingStudies = {} # Dictionary of imaging studies lists, by patient id 

    @classmethod
    def load(cls):
      """Loads patient imaging studies"""
      
      # Loop through imaging studies and build patient imaging studies lists:
      probs = csv.reader(open(IMAGINGSTUDIES_FILE,'U'),dialect='excel-tab')
      # header = probs.next()
      header = next(probs)
      for prob in probs:
          cls(dict(zip(header,prob))) # Create a clinical note instance 

    def __init__(self,p):
        self.id = p['ID']
        self.pid = p['PID']
        self.study_title = p['STUDY_TITLE']
        self.study_date = p['STUDY_DATE']
        self.study_accession_number = p['STUDY_ACCESSION_NUMBER']
        self.study_modality = p['STUDY_MODALITY']
        self.study_oid = p['STUDY_OID']
        self.series_title = p['SERIES_TITLE']
        self.series_oid = p['SERIES_OID']
        self.image_title = p['IMAGE_TITLE']
        self.image_date = p['IMAGE_DATE']
        self.image_file_name = p['IMAGE_FILE_NAME']
        self.image_oid = p['IMAGE_OID']
        self.image_sop = p['IMAGE_SOP']
        
        # Append imaging_study to the patient's imaging studies list:
        if self.pid in  self.__class__.imagingStudies:
          self.__class__.imagingStudies[self.pid].append(self)
        else: self.__class__.imagingStudies[self.pid] = [self]

    def asTabString(self):
       """Returns a tab-separated string representation of a imaging_study"""
       dl = [self.pid, self.date, self.title]
       s = ""
       for v in dl:
         s += "%s\t"%v 
       return s[0:-1] # Throw away the last tab

if __name__== '__main__':

  parser = argparse.ArgumentParser(description='Test Data ImagingStudies Module')
  group = parser.add_mutually_exclusive_group()
  group.add_argument('--imagingstudies', 
          action='store_true', help='list all imaging studies')
  group.add_argument('--pid',nargs='?', const='v',
     help='display imaging studies for a given patient id (default=2169591)')
  args = parser.parse_args()
 
  ImagingStudy.load()
  if args.pid:
    if not args.pid in ImagingStudy.imagingStudies:
      parser.error("No results found for pid = %s"%args.pid)
    probs = ImagingStudy.imagingStudies[args.pid]
    for prob in probs: 
      print (prob.asTabString())
    

     
