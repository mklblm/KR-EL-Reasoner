# from reasoner_devmb_timers import ELReasoner
from reasoner_class import ELReasoner

reasoner = ELReasoner("pizza.owl", '"Margherita"')

print(reasoner.run())