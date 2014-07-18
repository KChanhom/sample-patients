import datetime
from patient import Patient
from med import Med
from problem import Problem
from procedure import Procedure
from refill import Refill
from lab import Lab
from immunization import Immunization
from vitals import VitalSigns
from familyhistory import FamilyHistory
from socialhistory import SocialHistory
import os
import uuid

from jinja2 import Environment, FileSystemLoader
template_env = Environment(loader=FileSystemLoader('fhir_templates'), autoescape=True)

SMOKINGCODES = {
    '428041000124106': 'Current some day smoker',
    '266919005': 'Never smoker',
    '449868002': 'Current every day smoker',
    '266927001': 'Unknown if ever smoked',
    '8517006': 'Former smoker'
}

base=0
def uid(resource_type=None):
    global base
    base += 1
    if (resource_type == None):
      return str(base)
    else:
      return "%s/%s"%(resource_type, str(base))

def getVital(v, vt):
  return {
    'date': v.timestamp[:10],
    'code': vt['uri'].split('/')[-1],
    'units': vt['unit'],
    'value': float(getattr(v, vt['name'])),
    'scale': 'Qn',
    'name': vt['name']
    }

class FHIRSamplePatient(object):
  def __init__(self, pid, path):
    self.path = path
    self.pid = pid
    
    return

  def writePatientData(self):

    pfile = open(os.path.join(self.path, "patient-%s.fhir-bundle.xml"%self.pid), "w")
    p = Patient.mpi[self.pid]

    now = datetime.datetime.now().isoformat()
    id = "Patient/%s"%self.pid
    pid = id

    print >>pfile, """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>SMART patient bundle for transactional posting</title>
  <id>urn:uuid:%s</id>
  <updated>%s</updated>
"""%(uid(), now)

    template = template_env.get_template('patient.xml')
    print >>pfile, template.render(dict(globals(), **locals()))

    bps = []
    othervitals = []

    if self.pid in VitalSigns.vitals:
      for v in  VitalSigns.vitals[self.pid]:
          for vt in VitalSigns.vitalTypes:
              try: 
                  othervitals.append(getVital(v, vt))
              except: pass
          try: 
              systolic = getVital(v, VitalSigns.systolic)
              diastolic = getVital(v, VitalSigns.diastolic)
              bp = systolic
              bp['systolic'] = int(systolic['value'])
              bp['diastolic'] = int(diastolic['value'])
              bps.append(bp)
          except: pass

    for bp in bps:
        systolicid = uid("Observation")
        diastolicid = uid("Observation")
        id = uid("Observation")
        template = template_env.get_template('blood_pressure.xml')
        print >>pfile, template.render(dict(globals(), **locals()))

        id = systolicid
        o = {
                "date": bp['date'],
                "code": "8480-6",
                "name": "Systolic blood pressure",
                "scale": "Qn",
                "value": bp['systolic'],
                "units": "mm[Hg]",
                "unitsCode": "mm[Hg]"
        }
        template = template_env.get_template('observation.xml')
        print >>pfile, template.render(dict(globals(), **locals()))

        id = diastolicid
        o = {
                "date": bp['date'],
                "code": "8462-4",
                "name": "Diastolic blood pressure",
                "scale": "Qn",
                "value": bp['diastolic'],
                "units": "mm[Hg]",
                "unitsCode": "mm[Hg]"
        }
        template = template_env.get_template('observation.xml')
        print >>pfile, template.render(dict(globals(), **locals()))
        
    template = template_env.get_template('observation.xml')
    for o in othervitals:
        id = uid("Observation")
        if "units" in o.keys():
           o["unitsCode"] = o["units"]
        print >>pfile, template.render(dict(globals(), **locals()))

    if self.pid in Lab.results:  
      for o in Lab.results[self.pid]:
        id = uid("Observation")
        print >>pfile, template.render(dict(globals(), **locals()))

    medtemplate = template_env.get_template('medication.xml')
    dispensetemplate = template_env.get_template('medication_dispense.xml')
    if self.pid in Med.meds:  
      for m in Med.meds[self.pid]:
        medid = id = uid("MedicationPrescription")
        print >>pfile, medtemplate.render(dict(globals(), **locals()))

        for f in Refill.refill_list(m.pid, m.rxn):
          id = uid("MedicationDispense")
          print >>pfile, dispensetemplate.render(dict(globals(), **locals()))

    template = template_env.get_template('condition.xml')
    if self.pid in Problem.problems:  
      for c in Problem.problems[self.pid]:
        id = uid("Condition")
        print >>pfile, template.render(dict(globals(), **locals()))
        
    template = template_env.get_template('procedure.xml')
    if self.pid in Procedure.procedures:  
      for w in Procedure.procedures[self.pid]:
        id = uid("Procedure")
        print >>pfile, template.render(dict(globals(), **locals()))
        
    template = template_env.get_template('immunization.xml')
    if self.pid in Immunization.immunizations:  
      for i in Immunization.immunizations[self.pid]:
        id = uid("Immunization")
        i.cvx_system, i.cvx_id = i.cvx.rsplit("#",1)
        i.cvx_system += "#"
        print >>pfile, template.render(dict(globals(), **locals()))

    template = template_env.get_template('family_history.xml')
    if self.pid in FamilyHistory.familyHistories:  
      for fh in FamilyHistory.familyHistories[self.pid]:
        id = uid("FamilyHistory")
        print >>pfile, template.render(dict(globals(), **locals()))
        
    template = template_env.get_template('smoking_status.xml')
    if self.pid in SocialHistory.socialHistories: 
        t = SocialHistory.socialHistories[self.pid]
        t.smokingStatusText = SMOKINGCODES[t.smokingStatusCode]
        id = uid("SocialHistory")
        print >>pfile, template.render(dict(globals(), **locals()))
    
    if p.gestage:
        template = template_env.get_template('observation.xml')
        o = {
            "date": p.dob,
            "code": "18185-9",
            "name": "Gestational age at birth",
            "scale": "Qn",
            "value": p.gestage,
            "units": "weeks",
            "unitsCode": "wk"
        }
        id = uid("Observation")
        print >>pfile, template.render(dict(globals(), **locals()))

    print >>pfile, "\n</feed>"
    pfile.close()
