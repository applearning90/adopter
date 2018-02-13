// multiple checkbox validation
// https://github.com/1000hz/bootstrap-validator/issues/96 
$('[data-toggle="validator"]').validator({
	custom: {
    	chktype: function ($el) {
    		// Return the value at the named data store for the FIRST element in the jQuery collection
    		// in this case "type"
    		var name = $el.data('chktype')

    		// closest returns the first single ancestor of the selected element that is a form element
    		// find then returns descendant elements of the selected element where name="type"
    		var $checkboxes = $el.closest('form').find('input[name="' + name + '"]')

    		// checks if one of the selected elements matches the selectorElement, i.e. is checked
    		// Returns true if there is at least one match from the given argument, and false if not.
    		return $checkboxes.is(':checked')
    	},
    	chkage: function ($el) {
    		var name = $el.data('chkage')
    		var $checkboxes = $el.closest('form').find('input[name="' + name + '"]')

    		return $checkboxes.is(':checked')
    	},
    	chksize: function ($el) {
    		var name = $el.data('chksize')
    		var $checkboxes = $el.closest('form').find('input[name="' + name + '"]')

    		return $checkboxes.is(':checked')
    	}
  	},
	errors: {
  		chktype: 'Please select at least one type option',
  		chkage: 'Please select at least one age option',
  		chksize: 'Please select at least one size option'
	}
}).on('change.bs.validator', '[data-chktype], [data-chkage], [data-chksize]', function (e) {
	// on() method attaches one or more event handlers for the selected elements and child elements
	// $(selector).on(event,childSelector,data,function,map)
	// childSelector: Specifies that the event handler should only be attached to the specified child elements 

	// returns the element that triggered the event, in this case the form
	var $el  = $(e.target)

	var type = $el.data('chktype')
	var age = $el.data('chkage')
	var size = $el.data('chksize')

	var $type_checkboxes = $el.closest('form').find('input[name="' + type + '"]')
	var $age_checkboxes = $el.closest('form').find('input[name="' + age + '"]')
	var $size_checkboxes = $el.closest('form').find('input[name="' + size + '"]')

	$type_checkboxes.not(':checked').trigger('input')
	$age_checkboxes.not(':checked').trigger('input')
	$size_checkboxes.not(':checked').trigger('input')
}) 

