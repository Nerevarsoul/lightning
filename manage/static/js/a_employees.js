
// start operation
(function ($) {
    $(function () {

        // adding csrf-token in ajax
        var csrf_token = $("meta[name=csrf-token]").attr("content");
        $.ajaxSetup({
            beforeSend: function(xhr, settings) {
                if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                    xhr.setRequestHeader("X-CSRFToken", csrf_token)
                }
            }
        });

        //delete button
        $(document).on("click", ".delete", function(e) {
            e.preventDefault();
            var url = $(this).attr("href");
            var employee = $(this).closest("tr");
            var employee_id = employee.attr("class");

            $.ajax({
                type: "POST",
                url: url,
                dataType: "json",
                data: ({"employee_id": employee_id}),
                success: function (response) {
                    if (response["status"]==="success") {
                        employee.remove();
                    }   
                }
            });
        });

    });
})(jQuery);



