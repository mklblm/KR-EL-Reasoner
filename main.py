from reasoner_devmb_timers import ELReasoner
# from reasoner_class import ELReasoner

reasoner = ELReasoner("curry_ontolgoy.rdf", '"ButterChicken"')

print(reasoner.run())