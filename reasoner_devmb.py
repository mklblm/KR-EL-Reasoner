from collections import defaultdict
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

        # Attributes to keep track of during runs
        self.top = self.contains_top(self.ontology)
        self.subsumee = self.el_factory.getConceptName(class_name)
        self.GCIs = self.get_GCIs()

        # keep track of last individual added (individuals are integers)
        self.last_individual = 0
        self.initial_concepts = {}
        self.blocked_individuals = set()
        self.interpretation = defaultdict(set)
        self.roles_successors = defaultdict(lambda: defaultdict(set))

    def contains_top(self, ontology):
        all_concepts = ontology.getSubConcepts()

        for concept in all_concepts:
            concept_type = concept.getClass().getSimpleName()

            if concept_type == "TopConcept$":
                return concept

        return False

    def get_GCIs(self):
        GCIs = defaultdict(set)

        for axiom in self.axioms:
            axiom_type = axiom.getClass().getSimpleName()
            if axiom_type == "GeneralConceptInclusion":
                GCIs[axiom.lhs()].add(axiom.rhs())
            elif axiom_type == "EquivalenceAxiom":
                axiom_concepts = axiom.getConcepts().toArray()
                GCIs[axiom_concepts[0]].add(axiom_concepts[1])
                GCIs[axiom_concepts[1]].add(axiom_concepts[0])

        return GCIs

    def top_rule(self, individual):
        """
        Add top to this individual, only if top occurs in tbox.
        """
        if self.top:
            self.interpretation[individual].add(self.top)
            return False

    def intersect_rule_1(self, individual, concept):
        """
        Add the conjuncts of all conjunctions assigned to this individual to
        the individual as well.
        """
        add_concepts = set()
        changed = False

        # find conjunctions in individual
        for conjunct in concept.getConjuncts():
            # assign the conjuncts of this conjunction to individual (if not already present)
            if conjunct not in self.interpretation[individual]:
                add_concepts.add(conjunct)
                changed = True

        self.interpretation[individual].update(add_concepts)

        return changed

    def intersect_rule_2(self, individual, concept):
        """
        For all combinations of concepts in individual, also add the conjunction to the
        individual. Only do this if the conjunction appears in the Tbox.
        """
        add_concepts = set()
        changed = False

        # get all combinations of 2 for the concepts of this individual
        individual_concepts = list(self.interpretation[individual])
        # Don't need to check for combinations of individual with itself
        all_combinations = [(concept, ind) for ind in individual_concepts if ind != concept]

        # create a conjunction for all combinations
        for combination in all_combinations:
            conjunction = self.el_factory.getConjunction(combination[0], combination[1])

            # assign the conjunction to the individual if it's also in Tbox and not assigned yet
            if conjunction in self.all_concepts and conjunction not in self.interpretation[individual]:
                add_concepts.add(conjunction)
                changed = True

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
        # E-rule 2: If d has an r-successor with C assigned, add Er.C to d
        add_concepts = set()
        changed = False

        for role, successors in self.roles_successors[individual].items():
            for successor in successors:
                for concept in self.interpretation[successor]:
                    existential = self.el_factory.getExistentialRoleRestriction(role, concept)
                    if existential in self.all_concepts and existential not in self.interpretation[individual]:
                        add_concepts.add(existential)
                        changed = True

        self.interpretation[individual].update(add_concepts)

        return changed

    def subsumption_rule(self, individual, concept):
        # Subsumption rule: If d has C assigned and C subsumes D, assign D to d
        previous_len = len(self.interpretation[individual])
        add_concepts = set()
        changed = False

        for concept in self.interpretation[individual]:
            add_concepts.update(self.GCIs[concept])

        self.interpretation[individual].update(add_concepts)

        current_len = len(self.interpretation[individual])

        if current_len > previous_len:
            changed = True

        return changed

    def apply_rules(self, individual):
        """
        A function that will apply all rules to individual
        """
        changes = []

        # top rule only applies if top in tbox:
        if self.top:
            changes.append(self.top_rule(individual))

        # all the rules that depend on for concept in interpretation[individual]:
        # Casting this to a list to fix a bug where the set was modified during iteration.
        for concept in list(self.interpretation[individual]):
            concept_type = concept.getClass().getSimpleName()

            # Intersect rule 1
            if concept_type == "ConceptConjunction":
                changes.append(self.intersect_rule_1(individual, concept))

            # Intersect rule 2
            changes.append(self.intersect_rule_2(individual, concept))

            # Exists rule 2
            if concept_type == "ExistentialRoleRestriction":
                changes.append(self.exists_rule_1(individual, concept))

            # Subsumption rule
            changes.append(self.subsumption_rule(individual, concept))

        # Exists rule 2 (Unchanged - not dependent on concepts in individual)
        changes.append(self.exists_rule_2(individual))

        return True in changes

    def get_blocked_individuals(self):
        """
        Function will check which individuals are blocked, and return this set.
        """
        for ind1, concepts1 in self.interpretation.items():
            for ind2, concepts2 in self.interpretation.items():
                if ind2 < ind1 and concepts1.issubset(concepts2):
                    self.blocked_individuals.add(ind1)

        return self.blocked_individuals

    def run(self):
        self.subsumers = []

        # Track execution time
        start_time = perf_counter()

        # reset attributes for this concept
        self.first_individual = 1
        self.last_individual = 1
        self.initial_concepts = {}
        self.blocked_individuals = set()
        self.interpretation = defaultdict(set)
        self.roles_successors = defaultdict(lambda: defaultdict(set))

        # 1. add initial indivdiual
        self.interpretation[self.first_individual].add(self.subsumee)

        # 2. set changed == True
        changed = True
        # 3. while changed == True
        while changed:
            # 3.1. set changed == False
            changed = False

            # 3.2. for every element d in the current interpretation:
            # 3.2.1. apply all the rules on d in all possible ways,
            # so that only concepts from the input get assigned
            for individual in list(self.interpretation.keys()):
                if individual not in self.get_blocked_individuals():
                    # 3.2.2. If a new element was added or a new concept was assigned:
                    # set changed == True
                    changed = self.apply_rules(individual)

        for concept in self.concept_names:
            # Uncomment to show current concept:
            # print(f"Found concept: {self.formatter.format(concept)}")

            # If D_0 was assigned to d_0, return True, else return False
            if concept in self.interpretation[self.first_individual]:
                self.subsumers.append(concept)

        # print the subsumers
        for x in self.subsumers:
            # Indexing to remove parentheses from print statement.
            print(self.formatter.format(x)[1:-1])
            # Note how this thing also prints "None" as the last subsumer, i assume this is Top.

        # TODO: Remove this debugging code
        # print(f"{self.subsumee} Subsumers: {[self.formatter.format(x) for x in self.subsumers]}")
        # print execution time
        # print(f"Total execution time: {perf_counter() - start_time:.4f} seconds")
        # return self.subsumers
