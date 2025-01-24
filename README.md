# VU Knowledge Representation - EL Reasoner

This repo contains a group project within the course [Knowledge Representation](https://research.vu.nl/en/courses/knowledge-representation-4) (2024-25). The task was to create an intelligent reasoning system based on Description Logic (DL) consisting of an ontology and a custom reasoner based on Efficient Reasoning (EL). The goal of this system was to query menu items of a restaurant - in our case the restaurant theme is Curry. 

### Curry Ontology 
The Curry ontology is inspired by the [pizza ontology](https://github.com/owlcs/pizza-ontology/blob/master/pizza.owl) and employs Attributive Concept Language with Complements (ALC). In addition, we enhanced the Curry ontology to go beyond the expressivity of ALC, for example through the use of transitive roles, inversion, and nominals. It is a consistent ontology and contains 260 axioms, 70 classes, eight roles, and four individuals. In addition, the ontology contains 107 subclasses, 11 equivalences and 14 disjoint classes. Examples of classes are MassamanCurry, CurryIngredient, or Chicken. Examples of roles include hasCurryIngredient or hasSpiciness. More examples of the Curry ontology can be found in the report.   

### EL reasoner 


### Report
The report contains further details on the structure of reasoner and ontology and provides a nuanced perspective on challenges. In addition, we evaluate how the expressivity of the Curry ontology requires a similar level of expressivity from the reasoner. While EL reasoners are popular due to their efficiency in the case of this small ontology it is more pragmatic to apply reasoners such as HermiT, which allow for higher expressivity, thus more sophisticated queries. 


## Getting Started

These instructions will give you a copy of the project up and running on
your local machine.

### Prerequisites

Requirements for the software and other tools to build, test and push 
- [Python 3.10](https://www.python.org/downloads/) or higher
- [Java 23](https://www.oracle.com/java/technologies/downloads/)

### Installing

This codebase was programmed using python 3.10.1. The requirements.txt file contains all the need packages to run the code succesfully. 

Download this code base by running the following line in your terminal:

```git clone https://github.com/mklblm/KR-EL-Reasoner```

Install all required packages by running the following line in your terminal:

```pip install -r requirements.txt```

#### Java Gateway

This project was creating using the [dl4python library](https://github.com/PKoopmann/dl-lib). The libary is created specifically for the Knowledge Representation course at the Vrije Universiteit Amsterdam, in order for students to work with OWL ontologies in python instead of Java. In order to use dl4python, a number of preparation steps are necessary:

1. Make sure recent versions of Python and Java are installed.
2. Make sure Py4J is installed. This library is included in the requirements.txt file, and should thus be installed if all previous installation steps were followed. Alternatively, type the following command in the terminal:

    ```pip install py4j```

3. In order to use the dl4python library and run the EL Reasoner, a gateway server between Python and Java needs to be running. Do so by typing the following command in the terminal:

    ```java -jar dl4python-0.1.2-jar-with-dependencies.jar```

4. This gateway should be opened in the same folder as the python files using the dl4python library you want to run. Keep the gateway running while you want to run the python files. 

5. Open a new terminal to run the python files.

## Running the Reasoner

The EL reasoner can be run by calling the following command in the terminal:

```python main.py ontology_file_path class_name```

1. ontology_file_path should contain the path to an OWL ontology file.
2. class_name should contain the name of a class in the ontology file for which you want to find the subsumers.

### Example

Below is an example command that can be used to find the subsumers of the "Margherita" class in the pizza.owl file.

```python main.py ontologies/pizza.owl '"Margherita"'```

The output of this command will look like this:

CheesyPizza

Margherita

PizzaComUmNome

DomainThing

Pizza

Food

⊤

The printed classes are the found subsumers for the Margherita class. This list can be compared to the pizza ontology file itself.

Other examples can be run by replacting "Margherita" with any other named class, e.g. "Cajun" or "Caprina".

## Authors
  - Alexandra Genis
  - Daimy van Loo
  - Mikel Blom

See also the list of
[contributors](https://github.com/mklblm/KR-EL-Reasoner/graphs/contributors)
who participated in this project.

## License

This project is licensed under the [MIT](LICENSE.txt) License - see the [LICENSE.txt](LICENSE.txt) file for
details

## Acknowledgments

  - [Patrick Koopman](https://github.com/PKoopmann), the lecturer of Knowledge Representation, who has provided us with the dl4python files and documentation.

