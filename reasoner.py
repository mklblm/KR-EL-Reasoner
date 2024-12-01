from py4j.java_gateway import JavaGateway

# TODO: Need argparser to get the ontology file
ONTOLOGY_FILE = "pizza.owl"

## Setup java gateway and load the ontology
# connect to the java gateway of dl4python
gateway = JavaGateway()

# get a parser from OWL files to DL ontologies
parser = gateway.getOWLParser()

# get a formatter to print in nice DL format
formatter = gateway.getSimpleDLFormatter()

## --- // ----------------------------------------------------------------------------
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


## --- // ----------------------------------------------------------------------------
## EL Completion Rules
# Top Rule

# Intersect 1

# Intersect 2

# Exists rules 1: if d has Er.C assigned:
# E-rule 1.1:
# E-rule 1.2:

# E-rule 2:

# Subsumption rule:


## --- // ----------------------------------------------------------------------------
## EL Completion algorithm to decide whether O entails C subsumes D

# 1. start with initial assignment d_0, assign C_0 to it as initial concept
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


# Creating EL concepts and axioms

elFactory = gateway.getELFactory()
elk = gateway.getELKReasoner()
elk.setOntology(ontology)
