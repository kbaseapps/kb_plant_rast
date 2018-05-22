/*
A KBase module: kb_plant_rast
*/

module kb_plant_rast {

   typedef structure {
       string input_ws;
       string input_genome;
       string output_genome;
   } AnnotatePlantTranscriptsParams;

    typedef structure {
        string report_name;
        string report_ref;
    } AnnotatePlantTranscriptsResults;

    funcdef annotate_plant_transcripts(AnnotatePlantTranscriptsParams input) returns (AnnotatePlantTranscriptsResults output) authentication required;
};
