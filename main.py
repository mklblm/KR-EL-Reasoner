import argparse

# from reasoner_class import ELReasoner
from reasoner_devmb import ELReasoner

if __name__ == "__main__":
    # Set-up parsing command line arguments
    parser = argparse.ArgumentParser(description="Run EL reasoner and show subsumers for a given class name.")

    # Adding arguments
    parser.add_argument("ontology_file", help="Path to the ontology file in OWL format.")
    parser.add_argument("class_name", help="Class name to compute subsumers for. Write as: ClassName")

    # Read arguments from command line
    args = parser.parse_args()

    # Ensure class_name is in the correct form
    if not (args.class_name.startswith('"') and args.class_name.endswith('"')):
        args.class_name = f'"{args.class_name}"'

    # Create reasoner object
    reasoner = ELReasoner(args.ontology_file, args.class_name)

    # Run main with provide arguments
    print(reasoner.run())
