from dotmap import DotMap

config = dict(
    debug=True, # toggle for debugging prints/conditionals
    classifier_jar_flpth='/opt/rdp_classifier_2.12/dist/classifier.jar',
    propfile=dict(
        silva_138_ssu='/kb/module/data/SILVA_138_SSU_NR_99/rRNAClassifier.properties',
    )
)

Var = DotMap(config)

def reset_Var():
    Var.clear()
    Var.update(config)
