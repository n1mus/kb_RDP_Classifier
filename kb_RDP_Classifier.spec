/*
A KBase module: kb_RDP_Classifier
*/

module kb_RDP_Classifier {
    typedef structure {
        string report_name;
        string report_ref;
    } ReportResults;

    /*
        This example function accepts any number of parameters and returns results in a KBaseReport
    */
    funcdef classify(mapping<string,UnspecifiedObject> params) returns (ReportResults output) authentication required;

};
