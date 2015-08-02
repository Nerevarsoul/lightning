
// start operation
(function ($) {
    $(function () {

        // add date picker
        $.datepicker.setDefaults(
            $.extend($.datepicker.regional["ru"])
        );

        $(".date_picker").datepicker({
            dateFormat: 'dd-mm-yy',
            showAnim:'slide',
            showButtonPanel:true,
            changeMonth: true,
            changeYear: true
        });

        // clear filters uses button "clear"
        $("#clear").click(function() {

            $(".settings_data_fields input").each(function() {
                $(this).attr("value", "")
            });

            $(".settings_data option:selected").each(function() {
                $(this).removeAttr("selected")
            });

        });

    });
})(jQuery);



