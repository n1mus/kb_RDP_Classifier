from dotmap import DotMap

config = dict(
    debug=True, # toggle for debugging prints/conditionals
    classifierJar_flpth='/opt/rdp_classifier_2.12/dist/classifier.jar',
    train_propfile={
        'SILVA_138_SSU_NR_99': '/kb/module/data/SILVA_138_SSU_NR_99/rRNAClassifier.properties',
        'SILVA_138_SSU_NR_99_NCBI_taxonomy': '/kb/module/data/SILVA_138_SSU_NR_99_NCBI_taxonomy/rRNAClassifier.properties',
    },
)

Var = DotMap(config)

def reset_Var():
    Var.clear()
    Var.update(config)
