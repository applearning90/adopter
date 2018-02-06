$(function() {
        // preferences form validation
    $('#preferences').submit(function(){
        if (!$('.type').is(':checked')) {
            $('.type').attr('data-error', 'Please select at least one checkbox.');
        }
    });

});
