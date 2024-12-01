from py4j.java_gateway import JavaGateway
from collections import defaultdict

# TODO: Need argparser to get the ontology file
ONTOLOGY_FILE = "pizza.owl"

## Setup java gateway and load the ontology
# connect to the java gateway of dl4python
gateway = JavaGateway()

# get a parser from OWL files to DL ontologies
parser = gateway.getOWLParser()

# get a formatter to print in nice DL format
formatter = gateway.getSimpleDLFormatter()

## --- // -----------------------------------------------------------------------------
## Ontology parsing

print("Loading the ontology...")
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

# to create EL concepts
elFactory = gateway.getELFactory()

def has_top(all_concepts):
    for concept in all_concepts:
        concept_type = concept.getClass().getSimpleName()
        if concept_type == "TopConcept$":
             return True
    
    return False

ontology_has_top = has_top(allConcepts)

## --- // -----------------------------------------------------------------------------
## EL Completion Rules
# Top Rule: add top to every individual
def top_rule(individual, interpretation, ontology_has_top):
    """
    Add top to this individual, only if top occurs in tbox.
    """
    # not sure yet about this 'ontology_has_top' argument
    if ontology_has_top:
        interpretation[individual].add(elFactory.getTop())
        return True
    
    return False

# Intersect rule 1: If d has C intersection D assigned, assign also C and D to d


# Intersect rule 2: If d has C intersection D assigned, assign also C intersect D to d

# Exists rules 1: if d has Er.C assigned:
# E-rule 1.1: If there is an element e with initial concept C assigned, e the r-successor of d.
# E-rule 1.2: Otherwise, add a new r-successor to d, and assign to it as initla concept C.

# E-rule 2: If d has an r-successor with C assigned, add Er.C to d

# Subsumption rule: If d has C assigned and C subsumes D, assign D to d


## --- // -----------------------------------------------------------------------------
## EL Completion algorithm to decide whether O entails C subsumes D

# 1. start with initial in d_0, assign C_0 to it as initial concept
initial_concepts = {}
interpretation = defaultdict(set)

# 2. set changed == True
changed = True
# 3. while changed == True
while changed:
    # 3.1. set changed == False
    changed = False
    # 3.2. for every element d in the current interpretation:
    # 3.2.1. apply all the rules on d in all possible ways,
    # so that only concepts from the input get assigned

    # 3.2.2. If a new element was added or a new concept was assigned:
    # set changed == True

# If D_0 was assigned to d_0, return True, else return False