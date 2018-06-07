//csrftoken from cookie to ajax header
function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

function addUrlParameters(url, parameter) {
    var prefix = "?";
    if (url.includes(prefix)){
        prefix = "&";
    }
    return url + prefix + parameter
}

$(document).ready(function() {

    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", Cookies.get('csrftoken'));
            }
        }
    });

    /** Modal dialogues should be focused and draggable */
    $(document).on('shown.bs.modal', function(event){
        $(this).focus();
        $(this).find(".modal-dialog").draggable({handle: ".modal-header"});
        $(this).attr('data-backdrop', 'static');
    });

    /** When hiding a modal, try to remove it from activeModals */
    $(document).on('hidden.bs.modal', '.template-modal', function(event){
        $(this).trigger('ajax-view-modal.hide-active')
    });

    /** Modals may be closed by clicking element with class 'cancel-modal' */
    $(document).on('click', '.cancel-modal', function(event){
        event.preventDefault();
        $(this).parents('.template-modal').modal('hide');
    });

});

function shadeRGBColor(color, percent) {
    var f=color.split(","),t=percent<0?0:255,p=percent<0?percent*-1:percent,R=parseInt(f[0].slice(4)),G=parseInt(f[1]),B=parseInt(f[2]);
    return "rgb("+(Math.round((t-R)*p)+R)+","+(Math.round((t-G)*p)+G)+","+(Math.round((t-B)*p)+B)+")";
}