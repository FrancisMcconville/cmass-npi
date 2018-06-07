var MultiUpload = undefined;

function multiUploadInit($uploadInput){
    if (typeof MultiUpload === 'undefined'){
        MultiUpload = {
            target_url: $uploadInput.attr('href'),
            staged_files: {},
            uploadFile: function(fileToUpload){
                var data = new FormData();
                data.append(fileToUpload.file.name, fileToUpload.file);
                var $icon = fileToUpload.row.find($('.upload-status span'));
                var $remove_row_link = fileToUpload.row.find($('.delete-row'));
                var $delete_attachment_link = fileToUpload.row.find($('.deleteButton'));
                var $attachment_id_input = fileToUpload.row.find($('.attachment_id input'));
                $.ajax({
                    url: MultiUpload.target_url,
                    type: "post",
                    data: data,
                    processData: false,
                    contentType: false,
                    datatype: 'json',
                    success: function (data, status, xhttp) {
                        $icon.removeClass();
                        $icon.addClass('glyphicon glyphicon-saved');
                        $icon.attr('title', 'Uploaded Successfully');
                        $remove_row_link.addClass('hidden');
                        $delete_attachment_link.removeClass('hidden');
                        $attachment_id_input.val(data['files'][0].id)
                    },
                    error: function (request, status, errorThrown) {
                        $icon.removeClass();
                        $icon.addClass('glyphicon glyphicon-floppy-remove');
                        $icon.attr('title', 'Upload Failed');
                        MultiUpload.staged_files[fileToUpload.file.name] = fileToUpload;
                        $(document).trigger("stagedFilesChange");
                    }
                });
            },
            deleteFile: function(fileId, row){
                $.ajax({
                    url: "/configuration/attachment/"+fileId+"/delete",
                    type: "post",
                    datatype: 'json',
                    success: function (data, status, xhttp) {
                        row.find('.delete-row').click();
                    },
                    error: function (request, status, errorThrown) {
                        alert("Could not connect to server: \n"+errorThrown);
                    }
                });
            },
            stageFilesForUpload: function(files) {
                for (var i = 0; i < files.length; i++) {
                    var f = files[i];

                    // If the file hasn't been uploaded before
                    if (!MultiUpload.staged_files.hasOwnProperty(f.name)) {
                        $('.add-row').click();
                        var $new_row = $('tr.form-set:last');
                        $new_row.find($('td.file-name input')).val(f.name);
                        MultiUpload.staged_files[f.name] = {'row': $new_row, 'file': f};
                    } else {
                        alert("" + f.name + " is already staged for upload");
                    }
                }
                $('#multiUpload').val(undefined);
                $(document).trigger("stagedFilesChange");
            },
            uploadStagedFiles: function(){
                var files = $.extend(true, {}, MultiUpload.staged_files);
                MultiUpload.staged_files = {};

                for (var key in files){
                    var upload = files[key];
                    MultiUpload.uploadFile(upload);
                }
                $(document).trigger("stagedFilesChange");
            }
        }
    }
}


$(document).ready(function(){

    /** When the page loads, any attachment-row's which have been uploaded must have their remove row link hidden*/
    $('.attachment-row').each(function(row){
        if ($(this).find('.attachment_id input').val()){ $(this).find('.delete-row').addClass('hidden') }
    });

    // addFilesButton activated multiUpload input
    $("div[id='addFilesButton']").click(function () {
        $("input[id='multiUpload']").click();
    });

    /** User has selected files to be staged for upload */
    $("input[id='multiUpload']").change(function (e) {
        if(!e.target.files || typeof MultiUpload === 'undefined') return;
        MultiUpload.stageFilesForUpload(e.target.files);
    });

    /** User wishes to upload all staged files */
    $("div[id='uploadButton']").click(function () {
        if (typeof MultiUpload !== 'undefined'){ MultiUpload.uploadStagedFiles(); }
    });

    /** User is trying to delete an uploaded attachment */
    $(document).on('click', '.deleteButton', function () {
        if (typeof MultiUpload !== 'undefined'){
            var $row = $(this).closest('.form-set');
            var id = $row.find('.attachment_id input').val();
            MultiUpload.deleteFile(id, $row);
        }

    });

});

