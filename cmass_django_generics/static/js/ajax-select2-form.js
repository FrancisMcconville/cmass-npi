/** This script depends on ajax-view-modal.js */

$(document).ready(function(){
    /** enable updateEditButtons for select2 fields with values */
    $('.select2-edit-button').trigger('updateEditButton');

    /** select2Forms maps a modalID with the select2 ID which it's inputting for */
    if (typeof $.select2Forms === 'undefined'){ $.select2Forms = {} }
});

$(document).on('shown.bs.modal', function() {
    $('.select2-edit-button').trigger('updateEditButton');
});

$(document).on('click', '.select2-create-form', function(event){
    /**
    Sending a GET request with select2request argument will signal the controller to add
     select2-create-save class to submit buttons */
    event.preventDefault();
    var url = $(this).attr('href') + "?select2request=t";
    var select_id = "#"+$(this).siblings('select').attr('id');

    $.ajax({
        url: url,
        type: "get",
        datatype: 'json',
        success: function (data) {
            showModal(data.modal, data.template_selector, undefined);
            $.select2Forms[data.template_selector] = select_id;
        },
        error: function (request, status, errorThrown) {
            alert(errorThrown)
        }
    });
});

$(document).on('click', '.select2-create-save', function(event){
    /**
    Sending a POST request with select2request argument will signal the controller to reply with the created object */
    event.preventDefault();
    var $form = $(this).closest('.template-modal').find('form');
    var data = $form.serializeArray();
    var url = addUrlParameters($(this).attr('href'), 'select2request=t');

    $.ajax({
        url: url,
        type: "post",
        data: data,
        datatype: 'json',
        success: function (data, status, xhttp) {
            if (data.created_object) {
                var $select2 = $($.select2Forms[data.template_selector]);
                $select2.html(
                    "<option value=\"" + data.created_object + "\">\n" +
                        data.created_object_name +
                    "</option>"
                );
                $(data.template_selector).modal('hide');
                $select2.siblings('.select2-edit-button').trigger('updateEditButton');
                $select2.trigger('change');
            }
            else {
                showModal(data.modal, data.template_selector, undefined);
            }
        },
        error: function (request, status, errorThrown) {
            alert(errorThrown)
        }
    })
});

$(document).on('change', 'select[data-autocomplete-light-function="select2"]', function() {
    $(this).closest('tr').find('.select2-edit-button').trigger('updateEditButton')
});

$(document).on('updateEditButton', '.select2-edit-button', function(){
    /** Hides the edit button when select2 is empty. Updates the edit button's URL when the select2 value is updated */
    var $select2 = $(this).siblings('select');
    if ($select2.val()){
        $(this).prop('disabled', false);
        $(this).removeClass('hidden');
        var edit_url = $($select2).siblings('.select2-edit-url').attr('href');
        $(this).attr('href', edit_url.replace('0', $select2.val()));
    }
    else{
        $(this).prop('disabled', true);
        $(this).addClass('hidden');
    }
});