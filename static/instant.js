
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

            ul = $("<ul/>").attr({
                'id':'reslist',
                'data-role': 'listview',
                'class':"ui-listview",
            });

            ul.append($("<li/>").attr({
                'data-role':'list-divider',
                'class':'ui-li ui-li-divider ui-btn ui-bar-b ui-btn-up-undefined'
            }).html("Results"));

            $.each(ret, function(i, item) {
                t = $("<h3/>").attr({
                    'class':'ui-li-heading',
                }).html(item.token);
                f = $("<p/>").attr({'class':'ui-li-desc mono'})
                    .html(item.filename);
                $("<li/>").attr({
                    'class':'ui-li ui-li-static ui-btn-up-c mono',
                    'role':'option',
                }).append(t).append(f).appendTo(ul);
            });
            $("div#results").append(ul);
            $("ul").listview(refresh);
        });
    });
}

function init() {
    //blur_input_box("input#q", 'search');
    instantify("input#q", '');
}
