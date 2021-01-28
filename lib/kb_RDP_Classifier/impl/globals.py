'''
App globals and config
Useful so you don't have to clutter up function parameters
'''
from dotmap import DotMap

config = dict(
    debug=True, # toggle for debugging prints/conditionals/etc.

#------------------------------------------------- ref files

    classifier_jar_flpth='/opt/rdp_classifier_2.13/dist/classifier.jar',
    propfile=dict(
        silva_138_ssu='/kb/module/data/SILVA_138_SSU_NR_99/rRNAClassifier.properties',
    ),
#-------------------------------------------------- template

    report_template_flpth = '/kb/module/lib/kb_RDP_Classifier/template/report.html',


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

