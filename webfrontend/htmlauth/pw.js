$(document).ready(function(){

    $("#pwinput").focus();

    $("#pwcheck").click(function(){
        if ($("#pwcheck").is(":checked"))
        {
            $("#pwinput").clone()
            .attr("type", "text").insertAfter("#pwinput")
            .prev().remove();
        }
        else
        {
            $("#pwinput").clone()
            .attr("type","password").insertAfter("#pwinput")
            .prev().remove();
        }
    });
});