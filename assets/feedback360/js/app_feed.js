// This function gets cookie with a given name
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
var csrftoken = getCookie('csrftoken');

/*
The functions below will create a header with csrftoken
*/

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}
function sameOrigin(url) {
    // test that a given url is a same-origin URL
    // url could be relative or scheme relative or absolute
    var host = document.location.host; // host + port
    var protocol = document.location.protocol;
    var sr_origin = '//' + host;
    var origin = protocol + sr_origin;
    // Allow absolute or scheme relative URLs to same origin
    return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
        (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
        // or any other URL that isn't scheme relative or absolute i.e relative.
        !(/^(\/\/|http:|https:).*/.test(url));
}

$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type) && sameOrigin(settings.url)) {
            // Send the token to same-origin, relative URLs only.
            // Send the token only if the method warrants CSRF protection
            // Using the CSRFToken value acquired earlier
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});

/*
 General Functions
 */
function activateAsks() {
  $('.asks').addClass('active');
}
function deactivateAsks() {
  $('.asks').removeClass('active');
}

// create new snippet form (copy/paste the form in grid)
$('.application').on('click', '.button-content-invite', function() {
    var $formContent = $('#invite-form-content').html();
    var $parent = $(this).parent();
    // add infinite button add after click add ;)
    var $li4add = $(this).parent().parent();
    $('#container-invite-form').append($li4add.clone());
    // "creates" form copy/paste content
    $parent.html('');
    $parent.html($formContent);
});


$('.application').on('click', '.button-content-invite', function() {
    var $formContent = $('#invite-form-content').html();
    var $parent = $(this).parent();
    // add infinite button add after click add ;)
    var $li4add = $(this).parent().parent();
    $('#container-invite-form').append($li4add.clone());
    // "creates" form copy/paste content
    $parent.html('');
    $parent.html($formContent);
});

// catch submit() 'form snippet' add
$('.application').on('submit', '.add-form', function (event) {
    event.preventDefault();

    // basic validation. fields required
    var $social_name = $(this).find('input[name="social_name"]');
    var $proximity = $(this).find('select[name="proximity"]');

    if ( ($social_name.val().length <= 3) || ($proximity.val() == undefined) ) {
        alert("Preencha os dados para enviar!");
    } else {
        if ($social_name.prop('disabled') == true) {
            changeStatusFormEnable(this);
        } else {
            data = null;
            data = $(this).serialize();
            res = saveOneInvite(data);
            // disable form and return invited data
            changeStatusFormDisable(this);
        }
    }

});

// catch submit() 'form snippet'
$('.application').on('submit', '.del-form', function (event) {
    event.preventDefault();
    var $parent_li = $(this).parent().parent()
    // basic validation. fields required
    var $social_name = $(this).find('input[name="social_name"]');

    if ($social_name.val().length <= 3) {
        alert("Preencha os dados para enviar!");
    } else {
        if (confirm('Are you sure you want to remove this thing into the database?')) {
            // send it!
            data = null;
            data = $(this).serialize();
            delOneInvite(data);
            $(this).find("input[type=text], select").val("");
            $parent_li.fadeOut("slow");
            // $parent_li.hide();
        } else {
            // Do nothing!

        }

    }

});

// modifications of the status appearance
function changeStatusFormDisable(form) {
    var $parent = $(form).parent();
    var $input = $(form).find('input[name="social_name"]');
    var $select = $(form).find('select[name="proximity"]');
    var $button = $(form).find('input[type="submit"]');

    //effects UI
    $(form).fadeOut('slow');
    $(form).fadeIn('slow');

    $input.prop('disabled', true);
    $select.prop('disabled', true);

    var myTimer = window.setTimeout(function() {
        $button.addClass('success');
        $button.val('Salvo...');
    }, 200);

    $button.prop('disabled', false);
    var myTimer = window.setTimeout(function() {
        $button.val('Editar');
        $button.removeClass('success');
        $button.addClass('secondary');
    }, 500);

}

function changeStatusFormEnable(form) {
    // var $parent = $(form).parent();
    var $input = $(form).find('input[name="social_name"]');
    var $select = $(form).find('select[name="proximity"]');
    var $button = $(form).find('input[type="submit"]');

    //effects UI
    // $(form).fadeOut('fast');
    $(form).fadeIn('fast');

    $input.prop('disabled', false);
    $select.prop('disabled', false);
    $button.prop('disabled', false);

    var myTimer = window.setTimeout(function() {
        $button.val('Salvar');
        $button.removeClass('success');
    }, 500);

}

// Send form by ajax
response = null;

// add or save on database
var saveOneInvite = (function() {

    return function (data){
        $.post("/feedback360/invitation/add/", data)

            .done( function(response) {
             this.response = true;
                // alert("Certo");
        })
            .fail( function (response) {
                this.response = false;
                // alert("Feio");
        });
    };

})();

// remove or delete on database
var delOneInvite = (function() {

    return function (data){
        $.post("/feedback360/invitation/del/", data)

            .done( function(response) {
             this.response = true;
        })
            .fail( function (response) {
                this.response = false;
        });
    };

})();