from string import Template
from patient import Patient
from med import Med
from problem import Problem
from refill import Refill
from lab import Lab
from immunizations import Immunizations
from vitals import VitalSigns
import ontology_service
import os
import rdflib
                
class IndivoSamplePatient(object):
    """ Represents all of a patient's sample data in Indivo-compatible formats."""

    def __init__(self, pid, output_dir):
        self.pid = pid
        self.output_dir = output_dir
        self.p = Patient.mpi[self.pid]
        self.fullname = '%s %s'%(self.p.fname, self.p.lname)
        self.populated_p = False
        self.demographics_doc = None
        self.contact_doc = None
        self.data = []
        
    def _populate(self):
        """ parse the sample data into Indivo documents. """
        self.addDemographics()
        self.addContact()
        self.addLabs()
        self.addProblems()
        self.addMeds()
        self.addAllergies()
        self.addImmunizations()
        self.addVitals()
        self.populated_p = True
        
    def writePatientData(self):
        """Write a patient's data to an Indivo sample data profile under self.output_dir."""
        print "adding SMART data to data profile %s: %s"%(self.pid, self.fullname)
        
        if not self.populated_p:
            self._populate()
            
        # create a directory for the patient
        OUTPUT_DIR = os.path.join(self.output_dir, "patient_%s"%self.pid)
        try:
            os.mkdir(OUTPUT_DIR)

            # create a demographics file
            with open(os.path.join(OUTPUT_DIR, "Demographics.xml"), 'w') as demo:
                demo.write(self.demographics_doc)

            # create a contact document
            with open(os.path.join(OUTPUT_DIR, "Contact.xml"), 'w') as cont:
                cont.write(self.contact_doc)

            # create the rest of the data:
            for i, doc in enumerate(self.data):
                with open(os.path.join(OUTPUT_DIR, "doc_%s.xml"%i), 'w') as d:
                    d.write(doc)

        except OSError:
            print "Patient with id %s already exists, skipping..."%self.pid
    
    def addDemographics(self):
        """ Add demographics to the patient's data. """
        self.demographics_doc = DEMOGRAPHICS.substitute(dob=self.p.dob, gender=self.p.gender)

    def addContact(self):
        """ Add contact information to the patient's data. """
        p = self.p
        contact_data = {
            'fullname': self.fullname,
            'firstname': p.fname,
            'lastname': p.lname,
            'email': p.email,
            'street': p.street,
            'postal': p.zip,
            'city': p.city,
            'state': p.region,
            'country': p.country,
            'hphone': p.home,
            'cphone':p.cell,
            }
        self.contact_doc = CONTACT.substitute(**contact_data)

    def addLabs(self):
        """ Add labs to the patient's data. """
        if self.pid in Lab.results:  
            for l in Lab.results[self.pid]:
                try:
                    float_val = float(l.value)
                except Exception:
                    continue
                if l.scale != 'Qn':
                    self.data.append(
                        LAB.substitute(
                            date=l.date,
                            loinc=l.code,
                            name=l.name,
                            value=l.value,
                            units=l.units,
                            low=l.low,
                            high=l.high))

    def addProblems(self):
        """ Add problems to the patient's data. """
        if self.pid in Problem.problems: 
            for prob in Problem.problems[self.pid]:
                subs = {'end': {'end': '2010-09-13'}}
                self._set_default_attrs(prob, subs)
                prob_string = PROBLEM.substitute(
                    onset=prob.start,
                    resolution=prob.end,
                    snomed=prob.snomed, 
                    name=prob.name
                    )
                self.data.append(SDMX.substitute(models=prob_string))

    def addMeds(self):
        """ Add medications to the patient's data. """
        if  self.pid in Med.meds: 
            for m in Med.meds[self.pid]:

                # build the fills, setting some defaults
                subs = {
                    'qunit': {'qunit': '{tab}'},
                    'pbm': {'pbm': 'T00000000001011'},
                    'ncpdp': {'ncpdp': '5235235'},
                    'pharm_org': {'pharm_org': 'CVS #588'},
                    'pharm_co': {'pharm_co': 'Australia'},
                    'pharm_ci': {'pharm_ci': 'Wonder City'},
                    'pharm_pc': {'pharm_pc': '5555'},
                    'pharm_st': {'pharm_st': '111 Lake Drive'},
                    'pharm_re': {'pharm_re': 'West Australia'},
                    'prov_dea': {'prov_dea': '325555555'},
                    'prov_npi': {'prov_npi': '5235235'},
                    'prov_email': {'prov_email': 'jmandel@fake.emailserver.com'},
                    'prov_fn': {'prov_fn': 'Joshua'},
                    'prov_ln': {'prov_ln': 'Mandel'},
                    'prov_tel': {'prov_tel': '1-234-567-8910'},
                    }
                fills_str = ''
                for f in Refill.refill_list(self.pid, m.rxn):
                    self._set_default_attrs(f, subs)
                    fills_str = '\n'.join([fills_str, FULFILLMENT.substitute(
                                date=f.date,
                                days=f.days,
                                pbm=f.pbm,
                                ncpdp=f.ncpdp,
                                pharm_org=f.pharm_org,
                                pharm_co=f.pharm_co,
                                pharm_ci=f.pharm_ci,
                                pharm_pc=f.pharm_pc,
                                pharm_st=f.pharm_st,
                                pharm_re=f.pharm_re,
                                prov_dea=f.prov_dea,
                                prov_npi=f.prov_npi,
                                prov_email=f.prov_email,
                                prov_fn=f.prov_fn,
                                prov_ln=f.prov_ln,
                                prov_tel=f.prov_tel,
                                quantity=f.q,
                                quantityUnits=f.qunit
                                )])

                # build the med, setting some defaults
                subs = {
                    'qtt': {'qtt': 30, 'qttunit': '{tab}'},
                    'freq': {'freq':2, 'frequnit': '/d'},
                    'prov': {'prov': 'Derived by prescription', 'prov_id': 'prescription'},
                    'end': {'end': '2010-04-09'},
                    }
                self._set_default_attrs(m, subs)
                med_str = MEDICATION.substitute(
                    name=m.name,
                    rxnorm=m.rxn,
                    endDate=m.end,
                    frequencyValue=m.freq,
                    frequencyUnits=m.frequnit,
                    instructions=m.sig,
                    provenance=m.prov,
                    provenance_id=m.prov_id,
                    quantityValue=m.qtt,
                    quantityUnits=m.qttunit,
                    startDate=m.start,
                    fills=fills_str,
                    )
                                          
                self.data.append(SDMX.substitute(models=med_str))
    
    def addAllergies(self):
        """ Add allergies to the patient's data. Bogus data--doesn't read from an allergy file."""
        if int(self.pid)%100 < 85: # no allergies for ~ 85%
            exclusion = NO_ALLERGY.substitute(
                exclusion="no known allergies",
                exclusion_id="160244002",
                )
            self.data.append(SDMX.substitute(models=exclusion))
        else: # Sprinkle in some sulfa allergies
            al = DRUG_CLASS_ALLERGY.substitute(
                reaction="skin rash",
                reaction_id="271807003",
                category="drug allergy",
                category_id="416098002",
                allergen="sulfonamide antibacterial",
                allergen_id="N0000175503",
                severity="mild",
                severity_id="255604002",
                )
            self.data.append(SDMX.substitute(models=al))
            
            if int(self.pid)%2: # and throw in peanut allergies for every other patient
                al = FOOD_ALLERGY.substitute(
                    reaction="anaphylaxis",
                    reaction_id="39579001",
                    category="food allergy",
                    category_id="414285001",
                    allergen="peanut",
                    allergen_id="QE1QX6B99R",
                    severity="severe",
                    severity_id="24484000",
                    )
            self.data.append(SDMX.substitute(models=al))

    def addImmunizations(self):
        """ Add immunizations to the patient's data. """
        if self.pid in Immunizations.immunizations:
            for i in Immunizations.immunizations[self.pid]:
                tmp, adm_status, adm_status_id = self.coded_value(i.administration_status)
                tmp, prod_class_id = i.vg.rsplit("#", 1) if i.vg else ('', '')
                prod_class = i.vg_title or ''
                tmp, prod_class_2_id = i.vg2.rsplit("#", 1) if i.vg2 else ('', '')
                prod_class_2 = i.vg2_title or ''
                tmp, prod_name_id = i.cvx.rsplit("#", 1)
                prod_name = i.cvx_title
                tmp, ref, ref_id = self.coded_value(i.refusal_reason) if i.refusal_reason else ('', '', '')
                i_str = IMMUNIZATION.substitute(
                    date=i.date,
                    adm_status=adm_status,
                    adm_status_id=adm_status_id,
                    prod_class=prod_class,
                    prod_class_id=prod_class_id,
                    prod_class_2=prod_class_2,
                    prod_class_2_id=prod_class_2_id,
                    prod_name=prod_name,
                    prod_name_id=prod_name_id,
                    ref=ref,
                    ref_id=ref_id,
                    )
                self.data.append(SDMX.substitute(models=i_str))

    def addVitals(self):
        """ Add vitals to the patient's data. """

        def getBP(vt):
            """ Format a bloodPressure for templating into Vitals documents. """
            vt['indivo_prefix'] = 'bp_' + vt['name']
            return getVital(vt)
        
        def getVital(vt):
            """ Format a vitalSign for templating into Vitals documents. """

            if hasattr(v, vt['name']):
                val = getattr(v, vt['name'])
                sys, title, ident = self.coded_value(vt['uri'])
                return VITAL_SIGN.substitute(
                    prefix=vt['indivo_prefix'] if 'indivo_prefix' in vt else vt['name'],
                    unit=vt['unit'],
                    val=val,
                    name_title=title,
                    name_id=ident,
                    name_system=sys
                    )

        def cleanVitalsDate(date_str):
            """ Convert dates coming from raw Vitals data into UTC ISO8601 Timestamps."""
            if date_str[-1] != 'Z':
                date_str += 'Z'
            return date_str.replace(' ', 'T')
        
        if self.pid in VitalSigns.vitals:
            for v in VitalSigns.vitals[self.pid]:
                measurements = []
                for vt in VitalSigns.vitalTypes:
                    measurements.append(getVital(vt))

                if v.systolic:
                    measurements.append(getBP(VitalSigns.systolic))
                    measurements.append(getBP(VitalSigns.diastolic))

                encounter_str = ENCOUNTER.substitute(
                    start=cleanVitalsDate(v.start_date),
                    end=cleanVitalsDate(v.end_date),
                    encounterType=ENCOUNTER_TYPE.substitute() if v.encounter_type == 'ambulatory' else '',
                    )
                vitals_str = VITAL_SIGNS.substitute(
                    date=cleanVitalsDate(v.timestamp),
                    encounter=encounter_str,
                    vitals_str = ''.join(measurements),
                    )
                self.data.append(SDMX.substitute(models=vitals_str))

    def coded_value(self, raw_uri):
        """ Look up a URI in the ontology service. """
        g = rdflib.Graph()
        uri = rdflib.URIRef(raw_uri)
        cv = ontology_service.coded_value(g, rdflib.URIRef(uri))
        title = str(list(g.triples((uri, DCTERMS.title, None)))[0][2])
        sep = "#" if "#" in str(uri) else "/"
        sys, ident = str(uri).rsplit(sep, 1)
        return (sys+sep, title, ident)

    def _set_default_attrs(self, obj, subs):
        """ Set default attributes defined in *subs* on *obj* if they don't exist. """
        for attr_name, attr_subs in subs.iteritems():
            if not getattr(obj, attr_name, None):
                for newattr_name, newattr_val in attr_subs.iteritems():
                    setattr(obj, newattr_name, newattr_val)

###########################
# Constants and Templates #
###########################

DCTERMS = rdflib.Namespace('http://purl.org/dc/terms/')

SDMX = Template("""
<Models xmlns="http://indivo.org/vocab/xml/documents#">
$models
</Models>
""")

DEMOGRAPHICS = Template("""
<Demographics xmlns="http://indivo.org/vocab/xml/documents#">
    <dateOfBirth>$dob</dateOfBirth>
    <gender>$gender</gender>
    <language>EN</language>
</Demographics>
""")

MEDICATION = Template("""
<Model name="Medication">
  <Field name="drugName_title">$name</Field>
  <Field name="drugName_system">http://purl.bioontology.org/ontology/RXNORM/</Field>
  <Field name="drugName_identifier">$rxnorm</Field>
  <Field name="endDate">$endDate</Field>
  <Field name="frequency_value">$frequencyValue</Field>
  <Field name="frequency_unit">$frequencyUnits</Field>
  <Field name="instructions">$instructions</Field>
  <Field name="provenance_title">$provenance</Field>
  <Field name="provenance_system">http://smartplatforms.org/terms/codes/MedicationProvenance#</Field>
  <Field name="provenance_identifier">$provenance_id</Field>
  <Field name="quantity_value">$quantityValue</Field>
  <Field name="quantity_unit">$quantityUnits</Field>
  <Field name="startDate">$startDate</Field>
  <Field name="fulfillments">
    <Models>
      $fills
    </Models>
  </Field>
</Model>
""")

FULFILLMENT = Template("""
<Model name="Fill">
  <Field name="date">$date</Field>
  <Field name="dispenseDaysSupply">$days</Field>
  <Field name="pbm">$pbm</Field>
  <Field name="pharmacy_ncpdpid">$ncpdp</Field>
  <Field name="pharmacy_org">$pharm_org</Field>
  <Field name="pharmacy_adr_country">$pharm_co</Field>
  <Field name="pharmacy_adr_city">$pharm_ci</Field>
  <Field name="pharmacy_adr_postalcode">$pharm_pc</Field>
  <Field name="pharmacy_adr_street">$pharm_st</Field> 
  <Field name="pharmacy_adr_region">$pharm_re</Field> 
  <Field name="provider_dea_number">$prov_dea</Field>
  <Field name="provider_npi_number">$prov_npi</Field>
  <Field name="provider_email">$prov_email</Field>
  <Field name="provider_name_given">$prov_fn</Field>
  <Field name="provider_name_family">$prov_ln</Field>
  <Field name="provider_tel_1_type">w</Field>
  <Field name="provider_tel_1_number">$prov_tel</Field>
  <Field name="provider_tel_1_preferred_p">true</Field>
  <Field name="quantityDispensed_value">$quantity</Field>
  <Field name="quantityDispensed_unit">$quantityUnits</Field>
</Model>
""")

PROBLEM = Template("""
<Model name="Problem">
  <Field name="startDate">$onset</Field>
  <Field name="endDate">$resolution</Field>
  <Field name="name_title">$name</Field>
  <Field name="name_system">http://purl.bioontology.org/ontology/SNOMEDCT/</Field>
  <Field name="name_identifier">$snomed</Field>
</Model>
""")

DRUG_CLASS_ALLERGY = Template("""
<Model name="Allergy">
    <Field name="allergic_reaction_title">$reaction</Field>
    <Field name="allergic_reaction_system">http://purl.bioontology.org/ontology/SNOMEDCT/</Field>
    <Field name="allergic_reaction_identifier">$reaction_id</Field>
    <Field name="category_title">$category</Field>
    <Field name="category_system">http://purl.bioontology.org/ontology/SNOMEDCT/</Field>
    <Field name="category_identifier">$category_id</Field>
    <Field name="drug_class_allergen_title">$allergen</Field>
    <Field name="drug_class_allergen_system">http://purl.bioontology.org/ontology/NDFRT/</Field>
    <Field name="drug_class_allergen_identifier">$allergen_id</Field>
    <Field name="severity_title">$severity</Field>
    <Field name="severity_system">http://purl.bioontology.org/ontology/SNOMEDCT/</Field>
    <Field name="severity_identifier">$severity_id</Field>
</Model>
""")

FOOD_ALLERGY = Template("""
<Model name="Allergy">
    <Field name="allergic_reaction_title">$reaction</Field>
    <Field name="allergic_reaction_system">http://purl.bioontology.org/ontology/SNOMEDCT/</Field>
    <Field name="allergic_reaction_identifier">$reaction_id</Field>
    <Field name="category_title">$category</Field>
    <Field name="category_system">http://purl.bioontology.org/ontology/SNOMEDCT/</Field>
    <Field name="category_identifier">$category_id</Field>
    <Field name="food_allergen_title">$allergen</Field>
    <Field name="food_allergen_system">http://fda.gov/UNII/</Field>
    <Field name="food_allergen_identifier">$allergen_id</Field>
    <Field name="severity_title">$severity</Field>
    <Field name="severity_system">http://purl.bioontology.org/ontology/SNOMEDCT/</Field>
    <Field name="severity_identifier">$severity_id</Field>
</Model>
""")

NO_ALLERGY = Template("""
<Model name="AllergyExclusion">
    <Field name="name_title">$exclusion</Field>
    <Field name="name_identifier">$exclusion_id</Field>
    <Field name = "name_system">http://purl.bioontology.org/ontology/SNOMEDCT/</Field>
</Model>
""")

LAB = Template("""
<Lab xmlns="http://indivo.org/vocab/xml/documents#" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dateMeasured>${date}T00:00:00Z</dateMeasured>
  <labType>general</labType>

  <labTest xsi:type="SingleResultLabTest">
    <dateMeasured>${date}T00:00:00Z</dateMeasured>
    <name type="http://loinc.org/codes/"  value="$loinc"><![CDATA[$name]]></name>
    <final>true</final>
    <result xsi:type="ResultInRange">
      <valueAndUnit>
        <value>$value</value>
        <unit type="http://unitsofmeasure.org/" value="$units">$units</unit>
      </valueAndUnit>
      <normalRange>
        <minimum>$low</minimum>
        <maximum>$high</maximum>
        <unit type="http://unitsofmeasure.org/" value="$units">$units</unit>
      </normalRange>
    </result>    
  </labTest>
</Lab>
""")

CONTACT = Template("""
<Contact xmlns="http://indivo.org/vocab/xml/documents#">
  <name>
    <fullName>$fullname</fullName>
    <givenName>$firstname</givenName>
    <familyName>$lastname</familyName>
  </name>
  <email type="personal">
    <emailAddress>$email</emailAddress>
  </email>
  <address type="home">
    <streetAddress>$street</streetAddress>
    <postalCode>$postal</postalCode>
    <locality>$city</locality>
    <region>$state</region>
    <country>$country</country>
  </address>
  <phoneNumber type="home">$hphone</phoneNumber>
  <phoneNumber type="cell">$cphone</phoneNumber>
</Contact>
""")

IMMUNIZATION = Template("""
<Model name="Immunization">
    <Field name="date">$date</Field>
    <Field name="administration_status_title">$adm_status</Field>
    <Field name="administration_status_system">http://smartplatforms.org/terms/codes/ImmunizationAdministrationStatus#</Field>
    <Field name="administration_status_identifier">$adm_status_id</Field> 
    <Field name="product_class_title">$prod_class</Field>
    <Field name="product_class_system">http://www2a.cdc.gov/nip/IIS/IISStandards/vaccines.asp?rpt=vg#</Field>
    <Field name="product_class_identifier">$prod_class_id</Field>
    <Field name="product_class_2_title">$prod_class_2</Field>
    <Field name="product_class_2_system">http://www2a.cdc.gov/nip/IIS/IISStandards/vaccines.asp?rpt=vg#</Field>
    <Field name="product_class_2_identifier">$prod_class_2_id</Field>
    <Field name="product_name_title">$prod_name</Field>
    <Field name="product_name_system">http://www2a.cdc.gov/nip/IIS/IISStandards/vaccines.asp?rpt=cvx#</Field>
    <Field name="product_name_identifier">$prod_name_id</Field>
    <Field name="refusal_reason_title">$ref</Field>
    <Field name="refusal_reason_system">http://smartplatforms.org/terms/codes/ImmunizationRefusalReason#</Field>
    <Field name="refusal_reason_identifier">$ref_id</Field>
</Model>
""")

ENCOUNTER = Template("""
<Model name="Encounter">
    <Field name="startDate">$start</Field>
    <Field name="endDate">$end</Field>
    $encounterType
</Model>
""")

ENCOUNTER_TYPE = Template("""
    <Field name="encounterType_title">Ambulatory encounter</Field>
    <Field name="encounterType_system">http://smartplatforms.org/terms/codes/EncounterType#</Field>
    <Field name="encounterType_identifier">ambulatory</Field>
""")

VITAL_SIGNS = Template("""
<Model name="VitalSigns">
    <Field name="date">$date</Field>
    <Field name="encounter">$encounter</Field>
    $vitals_str
</Model>
""")

VITAL_SIGN = Template("""
<Field name="${prefix}_unit">$unit</Field>
<Field name="${prefix}_value">$val</Field>
<Field name="${prefix}_name_title">$name_title</Field>
<Field name="${prefix}_name_identifier">$name_id</Field>
<Field name="${prefix}_name_system">$name_system</Field>
""")
