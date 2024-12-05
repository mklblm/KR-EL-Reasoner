from collections import defaultdict
from itertools import combinations
from time import perf_counter

from py4j.java_gateway import JavaGateway


class ELReasoner:
    def __init__(self, ontology_file, class_name) -> None:
        ## Setup java gateway and load the ontology
        self.gateway = JavaGateway()

        # get a parser from OWL files to DL ontologies
        self.parser = self.gateway.getOWLParser()

        # get a formatter to print in nice DL format
        self.formatter = self.gateway.getSimpleDLFormatter()

        # load an ontology from a file
        self.ontology = self.parser.parseFile(ontology_file)

        # EL algorithm can only handle binary conjunctions
        self.gateway.convertToBinaryConjunctions(self.ontology)

        # get the TBox axioms
        self.tbox = self.ontology.tbox()
        self.axioms = self.tbox.getAxioms()

        # get all concepts occurring in the ontology and print
        self.all_concepts = self.ontology.getSubConcepts()

        # retrieve concept names and print
        self.concept_names = self.ontology.getConceptNames()

        # to create EL concepts
        self.el_factory = self.gateway.getELFactory()

        # initialize attributes for algorithm rum
        self.subsumee = self.el_factory.getConceptName(class_name)
        self.first_individual = 1
        self.last_individual = 1
        self.initial_concepts = {}
        self.blocked_individuals = set()
        self.interpretation = defaultdict(set)
        self.roles_successors = defaultdict(lambda: defaultdict(set))

        self.top = self.contains_top(self.ontology)
        self.GCIs = self.get_GCIs()

    def contains_top(self, ontology):
        """Function checks whether Top concept occurs in ontology.

        Returns:
            bool: True if Top occurs in docstring
        """
        all_concepts = ontology.getSubConcepts()

        # loop over all concepts and check if concept is Top.
        for concept in all_concepts:
            concept_type = concept.getClass().getSimpleName()

            if concept_type == "TopConcept$":
                return concept

        return False

    def get_GCIs(self):
        """Function creates a dictionary for all GCIs and Equivalence axioms
        in the ontology. The dictionary keys are the concepts on the left hand 
        side of the GCIs, the values are a set of all concepts that occur on
        the right hand side for the given key concept.

        Returns:
            Dict: Dictionary with left hand side concepts as keys, and a set of 
            right hand side concepts as value.
        """
        GCIs = defaultdict(set)

        for axiom in self.axioms:
            axiom_type = axiom.getClass().getSimpleName()

            # if GCI, just add right hand side to the set
            if axiom_type == "GeneralConceptInclusion":
                GCIs[axiom.lhs()].add(axiom.rhs())

            # if equivalence axiom, add both directions to dictionary
            elif axiom_type == "EquivalenceAxiom":
                axiom_concepts = axiom.getConcepts().toArray()
                GCIs[axiom_concepts[0]].add(axiom_concepts[1])
                GCIs[axiom_concepts[1]].add(axiom_concepts[0])

        return GCIs

    def top_rule(self, individual):
        """
        Assign top to this individual.
        """
        if self.top and self.el_factory.getTop() not in self.interpretation[individual]:
            self.interpretation[individual].add(self.top)
            return True
        
        return False

    def intersect_rule_1(self, individual, conjunction):
        """Assign the individual concepts of the conjunction
        to the individual in the representation

        Args:
            individual (int): integer representing individual
            concept : A conjunction concept

        Returns:
            bool: True if something actually changed.
        """
        add_concepts = set()
        changed = False

        for conjunct in conjunction.getConjuncts():

            # assign the conjuncts of this conjunction to individual (if not already present)
            if conjunct not in self.interpretation[individual]:
                add_concepts.add(conjunct)
                changed = True

        # add all conjuncts at once
        self.interpretation[individual].update(add_concepts)

        return changed

    def intersect_rule_2(self, individual):
        """For any combination of two concepts assigned to an individual,
        also assign the conjunction, but only if the conjunction occurs in the
        tbox.

        Args:
            individual (int): Integer representing the individual

        Returns:
            Bool: True if a conjunction was actually added.
        """
        add_concepts = set()
        changed = False

        # get all combinations of 2 for the concepts of this individual
        individual_concepts = list(self.interpretation[individual])
        all_combinations = combinations(individual_concepts, 2)

        #TODO: remove these lines if we def don't need it.
        # Don't need to check for combinations of individual with itself
        # all_combinations = [(concept, ind) for ind in individual_concepts if ind != concept]

        # create a conjunction for all combinations
        for combination in all_combinations:
            conjunction = self.el_factory.getConjunction(combination[0], combination[1])

            # assign the conjunction to the individual if it's also in Tbox and not assigned yet
            if conjunction in self.all_concepts and conjunction not in self.interpretation[individual]:
                add_concepts.add(conjunction)
                changed = True

        # add all conjunctions at once
        self.interpretation[individual].update(add_concepts)

        return changed

    def exists_rule_1(self, individual, concept):
        """
        # E-rule 1: If d has Er.C assigned, apply E-rules 1.1 and 1.2
        # E-rule 1.1: If there is an element e with initial concept C assigned, e the r-successor of d.
        # E-rule 1.2: Otherwise, add a new r-successor to d, and assign to it as initial concept C.
        """
        changed = False

        # "If d has Er.C assigned, apply E-rules 1.1 and 1.2"
        role_r = concept.role()  # r of Er.C
        concept_c = concept.filler()  # C of Er.C

        # E-rule 1.1:
        # If there is an element e with initial concept C assigned, e is the r-successor of d.
        if concept_c in self.initial_concepts:
            element_e = self.initial_concepts[concept_c]
            if role_r not in self.roles_successors[individual]:
                self.roles_successors[individual][role_r] = set()

            # only add the element if not already assigned
            if element_e not in self.roles_successors[individual][role_r]:
                self.roles_successors[individual][role_r].add(element_e)
                changed = True

        # E-rule 1.2:
        # Otherwise, add a new r-successor to d, and assign to it as initial concept C.
        else:
            self.last_individual += 1
            if role_r not in self.roles_successors[individual]:
                self.roles_successors[individual][role_r] = set()
            # "add a new r-successor to d"
            self.roles_successors[individual][role_r].add(self.last_individual)
            # "and assign to it as initial concept C."
            self.initial_concepts[concept_c] = self.last_individual
            self.interpretation[self.last_individual].add(concept_c)
            changed = True

        return changed

    def exists_rule_2(self, individual):
        """For each role succesor of the individual, assign the existential role restriction
        to this individual as well. Only if the existential concept occurs in the tbox.

        Args:
            individual (int): Integer representing the individual

        Returns:
            Bool: True if an existential role restriction was assigned
        """
        add_concepts = set()
        changed = False
        
        # loop over each succesor and their assigned concepts of the individual
        for role, successors in self.roles_successors[individual].items():
            for successor in successors:
                for concept in self.interpretation[successor]:
                    existential = self.el_factory.getExistentialRoleRestriction(role, concept)

                    # add the role restriction if not yet assigned, and it occurs in the tbox
                    if existential in self.all_concepts and existential not in self.interpretation[individual]:
                        add_concepts.add(existential)
                        changed = True

        # assign all role restrictions at once
        self.interpretation[individual].update(add_concepts)

        return changed

    def subsumption_rule(self, individual, concept):
        """Assign all subsumers of 'concept' to this individual as well.

        Args:
            individual (int): Integer representing an individual
            concept : Concept from which the subsumers should be assigned.

        Returns:
            Bool: True if subsumers were assigned to individual.
        """
        changed = False
        previous_len = len(self.interpretation[individual])

        # assign all subsumers
        self.interpretation[individual].update(self.GCIs[concept])

        current_len = len(self.interpretation[individual])

        # if individual now has more concepts assigned, the interpretation was changed
        if current_len > previous_len:
            changed = True

        return changed

    def apply_rules(self, individual):
        """Apply all the rules to this individual.

        Args:
            individual (int): Integer representing the individual

        Returns:
            Bool: True if any rule resulted in a change
        """
        changes = []

        # top rule only applies if top in tbox:
        if self.top:
            changes.append(self.top_rule(individual))

        # Intersect rule 2
        changes.append(self.intersect_rule_2(individual))

        # all the rules that depend on for concept in interpretation[individual]:
        # Casting this to a list to fix a bug where the set was modified during iteration.
        for concept in list(self.interpretation[individual]):
            concept_type = concept.getClass().getSimpleName()

            # Intersect rule 1
            if concept_type == "ConceptConjunction":
                changes.append(self.intersect_rule_1(individual, concept))

            # Exists rule 2
            if concept_type == "ExistentialRoleRestriction":
                changes.append(self.exists_rule_1(individual, concept))

            # Subsumption rule
            changes.append(self.subsumption_rule(individual, concept))

        # Exists rule 2 (Unchanged - not dependent on concepts in individual)
        changes.append(self.exists_rule_2(individual))

        return True in changes

    def get_blocked_individuals(self):
        """For each individual, check if they are blocked.

        Returns:
            set: Set of blocked individuals
        """

        # for any individual, if a previous individual has at least the same concepts
        # assigned, it is blocked
        for ind1, concepts1 in self.interpretation.items():
            for ind2, concepts2 in self.interpretation.items():
                if ind2 < ind1 and concepts1.issubset(concepts2):
                    self.blocked_individuals.add(ind1)

        return self.blocked_individuals
    
    def get_subsumers(self, interpretation):
        """Find and print all subsumers using the first individual from the interpretation.

        Args:
            interpretation (dict): Dictionary of indivdiuals and their assigned concepts
        """
        
        # loop over all concept names in ontology to check if they are subsumers of subsumee
        for concept in self.concept_names:
            
            # if the concept was assigned to first individual, it is a subsumer
            if concept in interpretation[self.first_individual]:
                self.subsumers.append(concept)

        # also check if top is a subsumer (if not, the ontology is not coherent)
        top = self.el_factory.getTop()
        if top in interpretation[self.first_individual]:
            self.subsumers.append(top)

        # print the subsumers
        for x in self.subsumers:
            print(self.formatter.format(x).strip('"'))

    def run(self):
        """Run the EL algorithm for self.ontology and self.subsumee, print the subsumers found for the
        subsumee.
        """
        self.subsumers = []
        
        # start interpretation with one individual with subsumee assigned
        self.interpretation[self.first_individual].add(self.subsumee)

        # to keep track of changes in interpretation
        changed = True

        # loop as long as interpretation changed
        while changed:
            
            # reset changed to check if applying rules will change interpretation
            changed = False
            changes = set()

            # apply all rules to every (non-blocked) individual in current interpretation
            for individual in list(self.interpretation.keys()):
                if individual not in self.get_blocked_individuals():
                    changes.add(self.apply_rules(individual))

            # if any rule made a change to interpretation
            changed = True in changes                    

        self.get_subsumers(self.interpretation)
