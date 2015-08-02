
// start operation
(function ($) {
    $(function () {

        // adding csrf-token in ajax
        var csrf_token = $('meta[name=csrf-token]').attr('content');
        $.ajaxSetup({
            beforeSend: function(xhr, settings) {
                if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                    xhr.setRequestHeader("X-CSRFToken", csrf_token)
                }
            }
        });

        // upload file
        $("input[class='add']").bind("click", function(e) {
            e.preventDefault()
            $(this).parent("form").find(".upload")[0].click();
        });
        $(".upload").bind("change", function() {
            $(this).parents("form").trigger("submit");
        });

        //operation button
        $(document).on("click", ".operation a", function(e) {
            e.preventDefault();
            var this_class = $(this).attr("class");
            var url = $(this).attr("href");
            var banner = $(this).closest("tr")
            var banner_id = banner.attr('id');

            // delete banner
            if (this_class == "delete") {

                $.ajax({
                    type: "POST",
                    url: url,
                    dataType: "json",
                    data: ({"banner_id": banner_id}),
                    success: function () {
                        if (!banner.prev(".banner").attr("id") && !banner.next(".banner").attr("id")) {
                            banner.after("<tr class='empty_result'><td colspan='7'><p>Баннеров не обнаружено</p></td></tr>");
                            $("#banner_buttons").remove();
                        };
                        banner.remove();
                    }
                });

            // up and down button
            } else {
                if (this_class == "up") {
                    var banner_goal = banner.prev(".banner")
                    var banner_goal_id = banner_goal.attr('id');
                } else {
                    var banner_goal = banner.next(".banner")
                    var banner_goal_id = banner_goal.attr('id');
                }

                $.ajax({
                    type: "POST",
                    url: url,
                    dataType: "json",
                    data: ({"banner_id": banner_id, "banner_goal_id": banner_goal_id}),
                    success: function () {
                        if (this_class == "up") {
                            banner_goal = banner_goal.detach();
                            banner.after(banner_goal);
                        } else {
                            banner = banner.detach();
                            banner_goal.after(banner);
                        }
                    }
                });
            }
        });



    });
})(jQuery);



