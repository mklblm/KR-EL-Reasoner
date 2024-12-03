from itertools import combinations

## --- // -----------------------------------------------------------------------------
## EL Completion Helper functions for Rules


def contains_top(self, ontology):
    all_concepts = ontology.getSubConcepts()

    for concept in all_concepts:
        concept_type = concept.getClass().getSimpleName()

        if concept_type == "TopConcept$":
            return True

    return False


# Usage Example:
# ontology_has_top = has_top(allConcepts)


## --- // -----------------------------------------------------------------------------
## EL Completion Rules


# Top Rule: add top to every individual
def top_rule(self, individual):
    """
    Add top to this individual, only if top occurs in tbox.
    """
    if self.ontology_contains_top:
        self.interpretation[individual].add(self.elFactory.getTop())
        return True

    return False


# Intersect rule 1: If d has C intersection D assigned, assign also C and D to d
def intersect_rule_1(self, individual):
    """
    Add the conjuncts of all conjunctions assigned to this individual to
    the individual as well.
    """
    changed = False

    for concept in self.interpretation[individual]:
        concept_type = concept.getClass().getSimpleName()

        # find conjunctions in individual
        if concept_type == "ConceptConjunction":
            for conjunct in concept.getConjuncts():
                # assign the conjuncts of this conjunction to individual (if not already present)
                if conjunct not in self.interpretation[individual]:
                    self.interpretation[individual].add(conjunct)
                    changed = True

    return changed


# Intersect rule 2: If d has C intersection D assigned, assign also C intersect D to d
def intersect_rule_2(self, individual):
    """
    For all combinations of concepts in individual, also add the conjunction to the
    individual. Only do this if the conjunction appears in the Tbox.
    """
    changed = False

    # get all combinations of 2 for the concepts of this individual
    individual_concepts = list(self.interpretation[individual])
    all_combinations = combinations(individual_concepts, 2)

    # create a conjunction for all combinations
    for combination in all_combinations:
        conjunction = self.elFactory.getConjunction(combination[0], combination[1])

        # assign the conjunction to the individual if it's also in Tbox and not assigned yet
        if conjunction in self.all_concepts and conjunction not in self.interpretation[individual]:
            self.interpretation[individual].add(conjunction)
            changed = True

    return changed


def exists_rule_1(self, individual):
    """
    # E-rule 1: If d has Er.C assigned, apply E-rules 1.1 and 1.2
    # E-rule 1.1: If there is an element e with initial concept C assigned, e the r-successor of d.
    # E-rule 1.2: Otherwise, add a new r-successor to d, and assign to it as initla concept C.
    """
    changed = False

    for concept in self.interpretation[individual]:
        concept_type = concept.getClass().getSimpleName()

        # "If d has Er.C assigned, apply E-rules 1.1 and 1.2"
        if concept_type == "ExistentialRoleRestriction":
            role_r = concept.role()  # r of Er.C
            concept_c = concept.filler()  # C of Er.C

            # E-rule 1.1:
            # If there is an element e with initial concept C assigned, e is the r-successor of d.
            if concept_c in self.initial_concepts:
                element_e = self.initial_concepts[concept_c]
                # TODO: is this check redundant?
                if role_r not in self.roles_successors[individual]:
                    self.roles_successors[individual][role_r] = set()
                self.roles_successors[individual][role_r].add(element_e)
                changed = True

            # E-rule 1.2:
            # Otherwise, add a new r-successor to d, and assign to it as initial concept C.
            else:
                # TODO: resolve this temp fix for indiviual
                new_individual = "d_1"
                if role_r not in self.roles_successors[individual]:
                    self.roles_successors[individual][role_r] = set()
                # "add a new r-successor to d"
                self.roles_successors[individual][role_r].add(new_individual)
                # "and assign to it as initial concept C."
                self.initial_concepts[concept_c] = new_individual
                changed = True

    return changed


def exists_rule_2(self, individual):
    # E-rule 2: If d has an r-successor with C assigned, add Er.C to d
    changed = False

    # TODO: I'm not sure if this is correct.
    for concept in self.interpretation[individual]:
        for role in self.roles_successors[individual]:
            if concept in self.roles_successors[individual][role]:
                self.interpretation[individual].add(self.elFactory.getExistentialRoleRestriction(role, concept))
                changed = True

    return changed


def subsumption_rule(self, individual):
    # Subsumption rule: If d has C assigned and C subsumes D, assign D to d
    changed = False

    # I tried putting more for-loops in here, i hope this is enough.
    for concept in self.interpretation[individual]:
        for subsumed_concept in self.all_concepts:
            for axiom in self.axioms:
                axiom_type = axiom.getClass().getSimpleName()
                if (
                    axiom_type == "GeneralConceptInclusion"
                    and axiom.lhs() == concept
                    and axiom.rhs() == subsumed_concept
                ):
                    self.interpretation[individual].add(subsumed_concept)
                    changed = True

    return changed
