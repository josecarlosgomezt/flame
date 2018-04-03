// parse results obtained from the prediction
function parseResults (results) {
    $("#data-body").text(results);

    var myjson = JSON.parse(results);

    var tbl_body = '<thead><tr><th>#mol</th><th>prediction</th></tr></thead>';
    var tbl_row;
    $.each(myjson, function() {
      tbl_row = "";

      $.each(this, function(k , v) {
        tbl_body += "<tr><td>"+(k+1)+"</td><td>"+v+"</td></tr>"; 
      })         

    })
    $("#data-table").html(tbl_body);   
};

// POST a prediction request for the selected model, version and input file
function postPredict (temp_dir, ifile) {
    // collect all data for the post and insert into postData object

    var version = $("#version option:selected").text();
    if (version=='dev') {
        version = '0';
    };

    $.post('/predict', {"ifile"   : ifile,
                        "model"   : $("#myselect option:selected").text(),
                        "version" : version,
                        "temp_dir": temp_dir
                        })
    .done(function(results) {
        parseResults (results)
    });
};

// main
$(document).ready(function() {

    // initialize button status to disabled on reload
    $("#predict").prop('disabled', true);


    // show file value after file select 
    $("#ifile").on('change',function(){
        file = document.getElementById("ifile").files[0];
        $("#ifile-label").html( file.name ); 
        $("#predict").prop('disabled', false);
    })


    // "predict" button
    $("#predict").click(function(e) {

        // make sure the browser can upload XMLHTTP requests
        if (!window.XMLHttpRequest) {
        $("#data-body").text("this browser does not support file upload");
            return;
        };

        // clear GUI
        $("#data-body").text('processing... please wait');
        $("#data-table").html('');
         
        // get the file 
        var ifile = document.getElementById("ifile").files[0];
        
        // generate a random dir name
        var temp_dir = randomDir();

        // call postPredict when file upload is completed
        if (upload(ifile, temp_dir, postPredict)==false) {
            $("#data-body").text("unable to upload file, prediction aborted...");
            return;
        };

        e.preventDefault(); // from predict click function
    });


});