//Sign up form
$("#registerForm").submit(function(e){
    var $form = $(this);
    var $error = $form.find(".error");
    var data = $form.serialize();
    if (data.password != data.confirm){
        $error.text("Passwords are not similar").removeClass("error--hidden");
        return;
        }
    else{
        $error.text("You have been registered").removeClass("error--hidden");
        return;
        }


    $.ajax({
        url: "/user/signup",
        type: "POST",
        data: data,
        dataType: "json",
        success: function(resp) {
            console.log(resp);
            window.location.href="/user";
        },
        error: function(resp){
            console.log(resp);
            $error.text(resp.responseJSON.message).removeClass("error--hidden");
        }
    });
    e.preventDefault();
});

//Login form
$("form[name=login_form]").submit(function(e){
    var $form = $(this);
    var $error = $form.find(".error");
    var data = $form.serialize();
    console.log(data);

    $.ajax({
        url: "/user/login",
        type: "POST",
        data: data,
        dataType: "json",
        success: function(resp) {
            console.log(resp);
            window.location.href="/dashboard";
        },
        error: function(resp){
            console.log(resp);
            $error.text(resp.responseJSON.message).removeClass("error--hidden");
        }
    });
    e.preventDefault();
});

