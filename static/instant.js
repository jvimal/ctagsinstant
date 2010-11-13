
var debug="#debug";

function blur_input_box(id, def) {
    $(id).click(function() {
        if(this.value == 'search')
            this.value = '';
    });

    $(id).blur(function() {
        if(this.value == '')
            this.value = 'search';
    });
}

function instantify(id, fn) {
    $(id).keyup(function() {
        $(debug).html("Search query: " + this.value);
        $.getJSON('/token/' + this.value, function(ret) {
            $("div#results").html("");
            $.each(ret, function(i, item) {
              $("<li/>").html(item.file + ": " + item.token).appendTo("div#results");
            });
        });
    });
}

function init() {
    blur_input_box("input#q", 'search');
    instantify("input#q", '');
}
