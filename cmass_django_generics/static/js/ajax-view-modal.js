/**
 * This Script will enable opening a view as a Bootstrap modal
 * An element with class 'ajax-view-link' and href attribute will make an ajax call to the server
 * The server is expected to reply with:
 *      JsonResponse({
 *          'modal': {string} HTML result from render_view_as_modal,
 *          'template_selector': {string} ID of the Modals HTML prefixed with a #
 *      })
 *
 * Forms opened in a Modal may be submitted by clicking an element with class 'modal-submit'
 * The POST url will be the form's action attribute by default, or the element's href attribute if provided
 * The server is expected to respond to this post with any of the following:
 *
 *      JsonResponse({
 *          'modal': {string} HTML result from render_view_as_modal,
 *          'template_selector': {string} ID of the Modals HTML prefixed with a #
 *      })
 *
 *      JsonResponse({'redirect': {string} URL to redirect to })
 *
 *      JsonResponse({'close_modal': {any} Close the current model if provided regardless of value})
 */

$(document).ready(function() {
    /** activeModals stores open modals in the order they were opened*/
    if (typeof $.activeModals === 'undefined') { $.activeModals = [] }
    /** modalRefreshUrls stores {modalID: URL to refresh} so that a modal can be refreshed */
    if (typeof $.modalRefreshUrls === 'undefined') { $.modalRefreshUrls = {} }
    /** ajax_refresh_page will be set to true by providing the template with {{ajax_refresh_page}} context */
    if (typeof $.ajax_refresh_page === 'undefined'){ $.ajax_refresh_page = false }

    /** GET view request */
    $(document).on('click', '.ajax-view-link', function(event){
        event.preventDefault();

        // TODO What is this doing??
        if($(this).attr('target') === '_blank') {
            return
        }

        getViewAsAjax($(this).attr('href'));
    });

    /** POST modal form request */
    $(document).on('click', '.modal-submit', function(event){
        event.preventDefault();
        submitModalWithAjax(this);
    });

    /** When hiding a modal, try to remove it from activeModals */
    $(document).on('ajax-view-modal.hide-active', '.template-modal', function(event){
        removeModalReferences("#"+$(this).attr('id'));
        $(this).remove();
        if ($.activeModals.length > 0) {
            var current_active_modal = $.activeModals[$.activeModals.length -1];
                console.log("is this where we are - 1");
            if (typeof current_active_modal !== 'undefined' &&
                typeof $.modalRefreshUrls[current_active_modal] !== 'undefined') {
                // Refresh now active view
                console.log("is this where we are");
                getViewAsAjax($.modalRefreshUrls[current_active_modal]);
            }
        }
        // If not more modals are open and refreshing this page is enabled, refresh the page.
        else if ($.ajax_refresh_page === true){ location.reload() }
    });

    /** Disable enter key submitting if it's within a .template-modal */
    $(document).ready(function () {
        $(window).keydown(function (event) {
            if ((event.keyCode === 13)) {
                if ($(event.target).parents('.template-modal').length){
                    event.preventDefault();
                }

            }
        });
    });

});

/**
 * Displays a modal, recording the oder of which it was opened by adding it to activeModals
 * @param {string} modalID - ID attribute of the modal to be refreshed.
 * @param {string} modalHtml - Updated HTML to be placed within the modal tags.
 * @param {string} url - URL which can be called to refresh the modal.
 *                          Optional argument. If not provided, modal will not be refreshed when it becomes active
 */
function showModal(modalHtml, modalID, url) {
    if (typeof url !== 'undefined'){$.modalRefreshUrls[modalID] = url;}

    // If modalID is already active, refresh it
    if ($.activeModals.indexOf(modalID) !== -1) {
        refreshModal(modalHtml, modalID);
    } else {
        if(typeof modalID !== 'undefined'){
            $.activeModals.push(modalID);
            $('body').append(modalHtml);
            $('body .template-modal:last').modal('show');
        }
    }
}

function removeModalReferences(modalID){
    delete $.modalRefreshUrls[modalID];
    var active_modal_index = $.activeModals.indexOf(modalID);
    if (active_modal_index !== -1){
        $.activeModals.splice(active_modal_index, 1);
    }
}

/**
 * Refreshes a modal's HTML and closes any modals opened in front of it.
 * @param {string} modalID - ID attribute of the modal to be refreshed.
 * @param {string} modalHtml - Updated HTML to be placed within the modal tags.
 */
function refreshModal(modalHtml, modalID){
    // Hide all modals opened in front of this modal
    for (var index = $.activeModals.indexOf(modalID) + 1; index < $.activeModals.length; index++){
        console.log("hiding "+$.activeModals[index]);
        $($.activeModals[index]).modal('hide');
    }
    // Reload modalHtml within modalID
    $(modalID).html($(modalHtml).unwrap().html());
}

/**
 * Django views expected to return a JsonResponse({
 *      'modal': {string} HTML result from render_view_as_modal,
 *      'template_selector': {string} ID of the Modals HTML prefixed with a #
 * })
 * @param {element} url - Server URL which will return the JsonResponse
 */
function getViewAsAjax(url){
    $.ajax({
        url: url,
        type: "get",
        datatype: 'json',
        success: function (data, status, xhttp) {
            console.log("getViewAsAjax success = ");
            console.log(data);
            if (typeof data.modal !== 'undefined' && typeof data.template_selector !== 'undefined'){
                showModal(data.modal, data.template_selector, data.refresh_url);
            }
            // TODO Else? What happens when modal or template_selector is null?
        },
        error: function (request, status, errorThrown) {
            alert(errorThrown)
        }
    });
}

/**
 * Submit a Form from a modal using Ajax
 * Server responses:
 *  When the Form contains errors, the server will return updated Modal HTML to refresh the modal
 *  When the Form validated successfully, the server may:
 *      Return a previously opened modal to refresh
 *      Close only the current modal
 *      Redirect the user to a different URL
 * @param {element} modal_submit_element - Element with class 'modal-submit'
 *      Expected to be contained within a parent with class .template-modal which also contains a form
 */
function submitModalWithAjax(modal_submit_element){
    var $modal = $(modal_submit_element).closest('.template-modal');
    var $form = $modal.find('form');
    var data = $form.serializeArray();

    // URL is form action by default, or the
    var url = $form.attr('action');
    if ($(modal_submit_element).attr('href'))
        url = $(modal_submit_element).attr('href');

    $.ajax({
        url: url,
        type: "post",
        data: data,
        datatype: 'json',
        success: function (data, status, xhttp) {
            if (data.redirect) {
                $(location).attr('href', data.redirect);
            } else if (data.close_modal) {
                var current_active_modal = $.activeModals[$.activeModals.length -1];
                $(current_active_modal).modal('hide');
            } else {
                showModal(data.modal, data.template_selector, url);
            }
        },
        error: function (request, status, errorThrown) {
            alert(errorThrown)
        }
    })
}

$(document).on("ajax-view-modal.update-links", ".template-modal", function(){
    $(".ajax-view-link-compatible").each(function(){
        $(this).addClass("ajax-view-link");
    })
});
