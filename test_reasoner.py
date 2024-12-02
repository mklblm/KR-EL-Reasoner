from reasoner_class import ELReasoner

reasoner = ELReasoner("pizza.owl", '"Margherita"')

print(reasoner.run())