'''
App globals and config
Useful so you don't have to clutter up function parameters
'''
from dotmap import DotMap

config = dict(
    debug=True, # toggle for debugging prints/conditionals/etc.

#------------------------------------------------- rdp files

    classifier_jar_flpth='/opt/rdp_classifier_2.13/dist/classifier.jar',
    propfile=dict(
        silva_138_ssu='/refdata/SILVA_138_SSU_parameters/rRNAClassifier.properties',
        silva_138_ssu_v4='/refdata/SILVA_138_SSU_V4_parameters/rRNAClassifier.properties',
    ),

#-------------------------------------------------- report

    report_template_flpth = '/kb/module/lib/kb_RDP_Classifier/template/report.html',
    report_height=533,


#-------------------------------------------------- 

    gene_id_2_name = dict(
        silva_138_ssu='SILVA 138 SSU',
    ),


)



''' DIRECTORY STRUCTURE

tmp/                                        `shared_folder`
└── kb_rdp_clsf_<uuid>/                      `run_dir`
    ├── return/                             `return_dir`
    |   ├── cmd.txt
    |   ├── study_seqs.fna
    |   └── RDP_Classifier_output/          `out_dir`
    |       ├── out_filterByConf.tsv
    |       └── out_fixedRank.tsv
    └── report/                             `report_dir`
        ├── fig
        |   ├── histogram.png
        |   ├── pie.png
        |   └── sunburst.png
        ├── histogram_plotly.html
        ├── pie_plotly.html
        ├── suburst_plotly.html
        └── report.html
'''

Var = DotMap(config)

def reset_Var():
    Var.clear()
    Var.update(config)

