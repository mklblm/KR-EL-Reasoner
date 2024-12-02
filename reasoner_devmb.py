from collections import defaultdict

from py4j.java_gateway import JavaGateway

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

## --- // -----------------------------------------------------------------------------
## Helper functions for EL Completion Rules


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
    if ontology_has_top:
        interpretation[individual].add(elFactory.getTop())
        return True

    return False


# Intersect rule 1: If d has C intersection D assigned, assign also C and D to d
def intersect_rule_1(individual, interpretation):
    """
    Add the conjuncts of all conjunctions assigned to this individual to
    the individual as well.
    """
    changed = False

    for concept in interpretation[individual]:
        concept_type = concept.getClass().getSimpleName()

        # find conjunctions in individual
        if concept_type == "ConceptConjunction":
            for conjunct in concept.getConjuncts():
                # assign the conjuncts of this conjunction to individual (if not already present)
                if conjunct not in interpretation[individual]:
                    interpretation[individual].add(conjunct)
                    changed = True

    return changed


# Intersect rule 2: If d has C intersection D assigned, assign also C intersect D to d
def intersect_rule_2(individual, interpretation, all_concepts):
    """
    For all combinations of concepts in individual, also add the conjunction to the
    individual. Only do this if the conjunction appears in the Tbox.
    """
    changed = False

    # get all combinations of 2 for the concepts of this individual
    individual_concepts = list(interpretation[individual])
    all_combinations = combinations(individual_concepts, 2)

    # create a conjunction for all combinations
    for combination in all_combinations:
        conjunction = elFactory.getConjunction(combination[0], combination[1])

        # assign the conjunction to the individual if it's also in Tbox and not assigned yet
        if conjunction in all_concepts and conjunction not in interpretation[individual]:
            interpretation[individual].add(conjunction)
            changed = True

    return changed


def exists_rule_1(individual, interpretation, initial_concepts, roles_successors):
    """
    # E-rule 1: If d has Er.C assigned, apply E-rules 1.1 and 1.2
    # E-rule 1.1: If there is an element e with initial concept C assigned, e the r-successor of d.
    # E-rule 1.2: Otherwise, add a new r-successor to d, and assign to it as initla concept C.
    """
    changed = False

    for concept in interpretation[individual]:
        concept_type = concept.getClass().getSimpleName()

        # "If d has Er.C assigned, apply E-rules 1.1 and 1.2"
        if concept_type == "ExistentialRoleRestriction":
            role_r = concept.role()  # r of Er.C
            concept_c = concept.filler()  # C of Er.C

            # E-rule 1.1:
            # If there is an element e with initial concept C assigned, e is the r-successor of d.
            if concept_c in initial_concepts:
                element_e = initial_concepts[concept_c]
                # TODO: is this check redundant?
                if role_r not in roles_successors[individual]:
                    roles_successors[individual][role_r] = set()
                roles_successors[individual][role_r].add(element_e)
                changed = True

            # E-rule 1.2:
            # Otherwise, add a new r-successor to d, and assign to it as initial concept C.
            else:
                # TODO: resolve this temp fix for indiviual
                new_individual = "d_1"
                if role_r not in roles_successors[individual]:
                    roles_successors[individual][role_r] = set()
                # "add a new r-successor to d"
                roles_successors[individual][role_r].add(new_individual)
                # "and assign to it as initial concept C."
                initial_concepts[concept_c] = new_individual
                changed = True

    return changed


def exists_rule_2(individual, interpretation, initial_concepts, roles_successors):
    # E-rule 2: If d has an r-successor with C assigned, add Er.C to d
    changed = False

    # TODO: I'm not sure if this is correct.
    for concept in interpretation[individual]:
        for role in roles_successors[individual]:
            if concept in roles_successors[individual][role]:
                interpretation[individual].add(elFactory.getExistentialRoleRestriction(role, concept))
                changed = True

    return changed


def subsumption_rule(individual, interpretation, allConcepts, axioms):
    # Subsumption rule: If d has C assigned and C subsumes D, assign D to d
    changed = False

    # I tried putting more for-loops in here, i hope this is enough.
    for concept in interpretation[individual]:
        for subsumed_concept in allConcepts:
            for axiom in axioms:
                axiom_type = axiom.getClass().getSimpleName()
                if (
                    axiom_type == "GeneralConceptInclusion"
                    and axiom.lhs() == concept
                    and axiom.rhs() == subsumed_concept
                ):
                    interpretation[individual].add(subsumed_concept)
                    changed = True

    return changed


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

# roles_successors: {individual : {role : {succesors}}}
roles_successors = defaultdict(defaultdict(set()))

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
