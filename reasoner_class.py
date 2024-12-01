from py4j.java_gateway import JavaGateway
from collections import defaultdict
from itertools import combinations

class ELReasoner():

    def __init__(self, ontology_file, class_name) -> None:
        ## Setup java gateway and load the ontology
        # connect to the java gateway of dl4python
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


        ### Attributes to keep track of during runs
        # store if ontology has top concept
        self.ontology_contains_top = self.contains_top(self.ontology)
        self.subsumee = self.elFactory.getConceptName(class_name)

        # keep track of last individual added (individuals are integers)
        self.last_individual = 0
        self.initial_concepts = {}
        self.blocked_individuals = set()
        self.interpretation = defaultdict(set)
        self.role_successors = defaultdict(defaultdict(set))
    
    def contains_top(self, ontology):
        all_concepts = ontology.getSubConcepts()

        for concept in all_concepts:
            concept_type = concept.getClass().getSimpleName()

            if concept_type == "TopConcept$":
                return True
    
        return False
    
    def top_rule(self, individual):
        """
        Add top to this individual, only if top occurs in tbox.
        """
        if self.ontology_contains_top:
            self.interpretation[individual].add(self.elFactory.getTop())
            return True
    
        return False
    
    def intersect_rule_1(self, individual):
        """
        Add the conjuncts of all conjunctions assigned to this individual to 
        the individual as well.
        """
        changed = False

        for concept in self.interpretation[individual]:
            concept_type = concept.getClass().getSimpleName()

            # find conjunctions in individual
            if concept_type == 'ConceptConjunction':
                for conjunct in concept.getConjuncts():

                    # assign the conjuncts of this conjunction to individual (if not already present)
                    if not conjunct in self.interpretation[individual]:
                        self.interpretation[individual].add(conjunct)
                        changed = True
        
        return changed
    
    def intesect_rule_2(self, individual):
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
            if conjunction in self.all_concepts and not conjunction in self.interpretation[individual]:
                self.interpretation[individual].add(conjunction)
                changed = True
        
        return changed
    
    def apply_rules(self, individual):
        """
        A function that will apply all rules to individual
        """
        pass

    def get_blocked_individuals(self, interpretation):
        pass

    def run(self):
        self.subsumers = []

        for concept in self.all_concepts:
            # reset attributes for this concept
            subsumer = concept
            self.first_individual = 1
            self.last_individual = 1
            self.initial_concepts = {}
            self.blocked_individuals = set()
            self.interpretation = defaultdict(set)
            self.role_successors = defaultdict(defaultdict(set))

            # 2. set changed == True
            changed = True
            # 3. while changed == True
            while changed:
                # 3.1. set changed == False
                changed = False

                # 3.2. for every element d in the current interpretation:
                # 3.2.1. apply all the rules on d in all possible ways,
                # so that only concepts from the input get assigned
                for individual in self.interpretation:
                    if individual in self.get_blocked_individuals(self.interpretation):

                        # 3.2.2. If a new element was added or a new concept was assigned:
                        # set changed == True
                        changed = self.apply_rules(individual)

            # If D_0 was assigned to d_0, return True, else return False
            if subsumer in self.interpretation[self.first_individual]:
                self.subsumers.append(subsumer)

        return self.subsumers



