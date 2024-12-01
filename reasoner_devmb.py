from py4j.java_gateway import JavaGateway
from collections import defaultdict


# TODO: Need argparser to get the ontology file
ONTOLOGY_FILE = "pizza.owl"
CLASS_NAME = "C"

## Setup java gateway and load the ontology
# connect to the java gateway of dl4python
gateway = JavaGateway()

# get a parser from OWL files to DL ontologies
parser = gateway.getOWLParser()

# get a formatter to print in nice DL format
formatter = gateway.getSimpleDLFormatter()

## --- // -----------------------------------------------------------------------------
## Ontology parsing

# load an ontology from a file
ontology = parser.parseFile(ONTOLOGY_FILE)

# EL algorithm can only handle binary conjunctions
gateway.convertToBinaryConjunctions(ontology)

# get the TBox axioms
tbox = ontology.tbox()
axioms = tbox.getAxioms()

# get all concepts occurring in the ontology and print
allConcepts = ontology.getSubConcepts()
# print([formatter.format(x) for x in allConcepts])

# retrieve concept names and print
conceptNames = ontology.getConceptNames()
# print([formatter.format(x) for x in conceptNames])

# allConcepts should be available as a global i guess? 
allConcepts = ontology.getSubConcepts()

def ontology_has_top(allConcepts):
    for concept in allConcepts:
        conceptType = concept.getClass().getSimpleName()
        if conceptType == "TopConcept$":
            return True 


## --- // -----------------------------------------------------------------------------
## EL Completion Rules

def top_rule(individual, interpretation):
    """
    Add top to this individual, only if top occurs in tbox.
    """
    # not sure yet about this 'ontology_has_top' argument
    if ontology_has_top:
        interpretation[individual].add(elFactory.getTop())
        return True
    
    return False
    
def intersect_rule_1(d):
    # Intersect rule 1: If d has C intersection D assigned, assign also C and D to d
    pass

def intersect_rule_2(d):
    # Intersect rule 2: If d has C intersection D assigned, assign also C intersect D to d
    pass

def exists_rule_1(d):
    # E-rule 1: If d has Er.C assigned, apply E-rules 1.1 and 1.2

        # E-rule 1.1: If there is an element e with initial concept C assigned, e the r-successor of d.

        # E-rule 1.2: Otherwise, add a new r-successor to d, and assign to it as initla concept C.
   pass

def exists_rule_2(d):
    # E-rule 2: If d has an r-successor with C assigned, add Er.C to d
    pass

def subsumption_rule(d):
    # Subsumption rule: If d has C assigned and C subsumes D, assign D to d
    pass


## --- // -----------------------------------------------------------------------------
## EL Completion algorithm to decide whether O entails C subsumes D

elFactory = gateway.getELFactory()

# 1. start with initial element d_0, assign C_0 to it as initial concept
d_0 = "d_0"
CLASS_NAME = "C"

# Initial concepts: Key = initial concept, Value = individual 
initial_concepts = defaultdict(str)

# interpretation: Key = individual, Value = set of Concepts
interpretation = defaultdict(set)

# Assign C to d_0, where C is the CLASS_NAME given at the commandline
initial_concepts[CLASS_NAME] = d_0
interpretation[d_0].add(CLASS_NAME)

# 2. set changed == True
changed = True
# 3. while changed == True
while changed:
    # 3.1. set changed == False
    changed = False
    # 3.2. for every element d in the current interpretation:
    for d in interpretation:
        print(d)
        # 3.2.1. apply all the rules on d in all possible ways,
        # so that only concepts from the input get assigned

        # 3.2.2. If a new element was added or a new concept was assigned:
        # set changed == True

# If D_0 was assigned to d_0, return True, else return False
