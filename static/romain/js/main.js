(function ($) {
    "use strict";

    function copyToClipboard(text) {
        if (window.clipboardData && window.clipboardData.setData) {
            // Internet Explorer-specific code path to prevent textarea being shown while dialog is visible.
            return window.clipboardData.setData("Text", text);

        } else if (document.queryCommandSupported && document.queryCommandSupported("copy")) {
            var textarea = document.createElement("textarea");
            textarea.textContent = text;
            textarea.style.position = "fixed";  // Prevent scrolling to bottom of page in Microsoft Edge.
            document.body.appendChild(textarea);
            textarea.select();
            try {
                return document.execCommand("copy");  // Security exception may be thrown by some browsers.
            } catch (ex) {
                console.warn("Copy to clipboard failed.", ex);
                return prompt("Copy to clipboard: Ctrl+C, Enter", text);
            } finally {
                document.body.removeChild(textarea);
            }
        }
    }

    function logout() {
        $.ajax({
            url: "/signout",
            type: "GET",
            success: function () {
                window.localStorage.removeItem("token");
                window.localStorage.removeItem("user");
                window.location.href = '/';
            },
            error: () => alert("Merci de verifier votre connexion"),
        });
    }

    // Check if user is logged
    var logged = window.localStorage.getItem("token") != null;
    var buttonContainer = $('.loginButtonContainer');
    if (logged) {
        buttonContainer.html('<a href="#" id="LogoutButton">Déconnexion</a>');
        $("#LogoutButton").click(logout);
        $('#UsernameHolder').html(JSON.parse(window.localStorage.getItem("user")).username);
        $('#tokenCopier').click(function () {
            copyToClipboard(window.localStorage.getItem('token'));
            alert("Votre token est copié, :)");
        });
    } else {
        buttonContainer.html('<a href="/user/">Se connecter</a>');
    }

    /*==================================================================
    [ Validate ]*/
    var input = $('.validate-input .input100');
    var input2 = $('.validate-signup .signup100');
    var input3 = $('.validate-delete-room .signup100');
    var input4 = $('.validate-add-room .signup100');

    $('.validate-form').on('submit', function () {
        var check = true;

        for (var i = 0; i < input.length; i++) {
            if (validate(input[i]) == false) {
                showValidate(input[i]);
                check = false;
            } else {
                // Ajouter login ici
                var $form = $(this);
                var data = $form.serialize();

                $.ajax({
                    url: "/user/login",
                    type: "POST",
                    data: data,
                    dataType: "json",
                    success: function (resp) {
                        window.localStorage.setItem("token", resp.token);
                        window.localStorage.setItem("user", JSON.stringify(resp.user));
                        window.location.href = "/dashboard";
                    },
                    error: function (resp) {
                        alert("Une erreur s'est produite")
                        console.log(resp);
                    }
                });
            }
        }
        return check;
    });
    //checking signup form and still didnt understand it
    $('.form-validate').on('submit', function () {
        var check = true;

        for (var i = 0; i < input2.length; i++) {
            if (validate2(input2[i]) == false) {
                showValidate2(input2[i]);
                check = false;

            } else {
                if ($(input2[i]).attr('name') != 'email') {
                    return false;
                } else {
                    // Ajouter signup ici
                    var data = $(this).serialize();
                    var showError = () => showValidate2(input2[i]);
                    if (data.pass2 != data.pass) {
                        alert("Passwords are not similar");
                        return;
                    } else {
                        $.ajax({
                            url: "/user/signup",
                            type: "POST",
                            data: data,
                            dataType: "json",
                            success: function () {
                                alert("Votre compte est créé");
                                document.getElementById("CompteCreé").style.visibility = "visible";
                            },
                            error: () => alert("Erreur"),
                        });
                        return;
                    }
                }
            }
        }

        return check;
    });


    //griser les boutons
    document.getElementById('Personnaliser').addEventListener('change', function () {
        // Collecter les champs
        var Temperature = $('#Temperature');
        var Son = $('#Son');
        var Luminosite = $('#Luminosite');
        var CO2 = $('#CO2');
        var Humidite = $('#Humidite');

        console.log('Evaluated checkbox at', peutPersonnaliser());
        // Voir si la valeur de personnaliser est True ou False pour activer ou desactiver les autres champs
        Temperature.prop("disabled", !peutPersonnaliser());
        Son.prop('disabled', !peutPersonnaliser());
        Luminosite.prop('disabled', !peutPersonnaliser());
        CO2.prop('disabled', !peutPersonnaliser());
        Humidite.prop('disabled', !peutPersonnaliser());

        if (!peutPersonnaliser()) {
            Temperature.prop('checked', true);
            Son.prop('checked', true);
            Luminosite.prop('checked', true);
            CO2.prop('checked', true);
            Humidite.prop('checked', true);

            $('#TemperatureSlider').addClass('switch-grey');
            $('#SonSlider').addClass('switch-grey');
            $('#LuminositeSlider').addClass('switch-grey');
            $('#CO2Slider').addClass('switch-grey');
            $('#HumiditeSlider').addClass('switch-grey');
        } else {

            $('#TemperatureSlider').removeClass('switch-grey');
            $('#SonSlider').removeClass('switch-grey');
            $('#LuminositeSlider').removeClass('switch-grey');
            $('#CO2Slider').removeClass('switch-grey');
            $('#HumiditeSlider').removeClass('switch-grey');
        }
    });

    function peutPersonnaliser() {
        return document.getElementById('Personnaliser').checked;
    }

    //fin griser les boutons


    $('.form-perso').on('submit', function () {
        var check = true;
        var params = collectParams();
        // Collecter le token
        var token = $('#token').val();
        console.log(token);
        //Ajouter appelle MDAP ici
        $.ajax({
            url: "https://aip-confort.milebits.com:3001/MADM?token={token}".replace('{token}', token),
            type: "POST",
            data: params,
            crossDomain: true,
            dataType: "json",
            success: function (resp) {
                var salles = resp['Resultat'];

                var items = "";

                salles.forEach(function (salle, index) {
                    var nom = Object.keys(salle)[0];
                    var donnees = salle[nom];

                    var temp = donnees['Temperature'];
                    var acoustic = donnees['Acoustique'];
                    var humidity = donnees['Humidite'];
                    var CO2 = donnees['CO2'];
                    var note = donnees['Note'];
                    var lum = donnees['Luminosite'];

                    var content = "Salle {NOM}".replace('{NOM}', nom);

                    var div = '<div style="text-align: center;" class="card"><div style="text-align: center;" class="card-header" id="Salle_{ID}_Heading"><h2 class="mb-0 text-center" style="text-align: center; width: 100%;"><button style="text-align: center;" class="btn btn-link btn-block text-left" type="button" data-toggle="collapse" data-target="#Salle_{ID}_Body" aria-expanded="false" aria-controls="Salle_{ID}_Body">{content} à {Note}/10 <div id="salle_rater_{ID}"></div></button></h2></div><div id="Salle_{ID}_Body" class="collapse" aria-labelledby="Salle_{ID}_Heading" data-parent="#DonneesClassementDiv"><div class="card-body"><div><strong>Temperature:</strong><span>{TEMPERATURE}</span></div><div><strong>Acoustique:</strong><span>{Acoustique}</span></div><div><strong>Humidite:</strong><span>{Humidite}</span></div><div><strong>Son:</strong><span>{Lum}</span></div><div><strong>CO2:</strong><span>{CO2}</span></div></div></div></div>';
                    div = div.replaceAll('{ID}', nom);
                    div = div.replaceAll('{content}', content);
                    div = div.replaceAll('{TEMPERATURE}', temp);
                    div = div.replaceAll('{Acoustique}', acoustic);
                    div = div.replaceAll('{Humidite}', humidity);
                    div = div.replaceAll('{CO2}', CO2);
                    div = div.replaceAll('{Lum}', lum);
                    div = div.replaceAll('{Note}', '        ' + note);
                    items = items + div;
                });
                $('#DonneesClassementDiv').html(items);
                salles.forEach(function (salle, index) {
                    var nom = Object.keys(salle)[0];
                    var donnees = salle[nom];
                    var note = donnees['Note'];
                    var rateBlock = $('#salle_rater_{ID}'.replaceAll('{ID}', nom));
                    console.log(rateBlock[0]);
                    var myRater = raterJs({
                        element: rateBlock[0],
                        rateCallback: function (rating, done) {
                            myRater.disable();
                            done();
                        },
                        readOnly: true,
                    });
                    myRater.setRating(note * 0.5);
                });
            },
            error: function (resp) {
                console.log(resp);
                $error.text(resp.responseJSON.message).removeClass("error--hidden");
            }
        });
        return check;
    });

    function collectParams() {
        var Temperature = document.getElementById("Temperature").checked;
        var Son = document.getElementById("Son").checked;
        var Luminosite = document.getElementById("Luminosite").checked;
        var CO2 = document.getElementById("CO2").checked;
        var Humidite = document.getElementById("Humidite").checked;
        var data = {
            "demandeTemperature": Temperature,
            "demandeAcoustique": Son,
            "demandeLuminosite": Luminosite,
            "demandeCO2": CO2,
            "demandeHumidite": Humidite
        };
        return data;
    }

    $('.form-delete-room').on('submit', function () {
        var check = true;
        for (var i = 0; i < input3.length; i++) {
            if (validate3(input3[i]) == false) {
                showValidate3(input3[i]);
                check = false;
            } else {

                // Ajouter supprimer salle ici
                var Salle = document.getElementById("salle").value;
                Salle = {
                    "Salle": Salle
                }

                var token = $('#token').val();
                var url = "https://aip-confort.milebits.com:3001/supprimerSalle?token={token}".replace('{token}', token);
                $.ajax({
                    url: url,
                    type: "POST",
                    dataType: "json",
                    data: Salle,
                    success: () => alert("La salle a été supprimée"),
                    error: () => alert("Aucune salle existente ne posséde ce nom"),
                    "headers": {"Access-Control-Allow-Origin": "*"}
                });
            }
        }

        return check;
    });

    $('.form-add-room').on('submit', function () {
        var check = true;
        for (var i = 0; i < input4.length; i++) {
            if (validate4(input4[i]) == false) {
                showValidate4(input4[i]);
                check = false;
            } else {
                // Ajouter ajouter salle ici
                Add_Room()

            }
        }

        return check;
    });


    $('.validate-form .input100').each(function () {
        $(this).focus(function () {
            hideValidate(this);
        });
    });

    $('.form-validate .signup100').each(function () {
        $(this).focus(function () {
            hideValidate(this);
        });
    });

    $('.form-delete-room .signup100').each(function () {
        $(this).focus(function () {
            hideValidate(this);
        });
    });

    $('.form-add-room .signup100').each(function () {
        $(this).focus(function () {
            hideValidate(this);
        });
    });

    function validate(input) {
        if ($(input).attr('type') == 'email' || $(input).attr('name') == 'email') {
            if ($(input).val().trim().match(/^([a-zA-Z0-9_\-\.]+)@(admin\.)*univ-lorraine.fr$/) == null) {
                return false;
            }
        } else {
            if ($(input).val().trim() == '') {
                return false;
            }
        }
    }

    function validate2(input2) {

        if ($(input2).attr('type') == 'email' || $(input2).attr('name') == 'email') {
            if ($(input2).val().trim().match(/^([a-zA-Z0-9_\-\.]+)@(admin\.)*univ-lorraine.fr$/) == null) {
                return false;
            } else {

                if (validate_mdp() == false) {
                    if ($(input2).attr('id') == 'Spsw2') {
                        showValidate2(input2);
                    }
                    return false;
                } else {
                }

            }
        } else {
            if ($(input2).val().trim() == '') {
                showValidate2(input2);
                return false;

            }
            if (validate_mdp() == false) {
                if ($(input2).attr('id') == 'Spsw2') {
                    showValidate2(input2);
                }
                return false;
            }

        }
    }

    function validate3(input3) {

        if ($(input3).attr('type') == 'salle' || $(input3).attr('name') == 'salle') {
            if ($(input3).val().trim().match(/^(S\d\d\d)$/) == null) {
                return false;
            } else {

            }
        } else {
            if ($(input3).val().trim() == '') {
                return false;
            }
        }
    }

    function validate4(input4) {

        if ($(input4).attr('type') == 'salle' || $(input4).attr('name') == 'salle') {
            if ($(input4).val().trim().match(/^(S\d\d\d)$/) == null) {
                return false;
            } else {

            }
        } else {
            if ($(input4).val().trim() == '') {
                return false;
            }
        }
    }


    function showValidate(input) {
        var thisAlert = $(input).parent();

        $(thisAlert).addClass('alert-validate');
    }

    function showValidate2(input2) {
        var thisAlert = $(input2).parent();

        $(thisAlert).addClass('alert-validate');
    }

    function showValidate3(input3) {
        var thisAlert = $(input3).parent();

        $(thisAlert).addClass('alert-validate');
    }

    function showValidate4(input4) {
        var thisAlert = $(input4).parent();

        $(thisAlert).addClass('alert-validate');
    }


    function hideValidate(input) {
        var thisAlert = $(input).parent();

        $(thisAlert).removeClass('alert-validate');
    }

    function hideValidate2(input2) {
        var thisAlert = $(input2).parent();

        $(thisAlert).removeClass('alert-validate');
    }

    function hideValidate3(input3) {
        var thisAlert = $(input3).parent();

        $(thisAlert).removeClass('alert-validate');
    }

    function hideValidate4(input4) {
        var thisAlert = $(input4).parent();

        $(thisAlert).removeClass('alert-validate');
    }


    function RedirectionJavascript() {
        document.location.href = "https://aip-confort.milebits.com:3001";
    }

    function submitbtn() {
        var Temperature = document.getElementById("Temperature").checked;
        var Son = document.getElementById("Son").checked;
        var Luminosite = document.getElementById("Luminosite").checked;
        var CO2 = document.getElementById("CO2").checked;
        var Humidite = document.getElementById("Humidite").checked;
    }

    function Add_Room() {
        var Salle = document.getElementById("ADSSalle").value;
        var Temperature = document.getElementById("ADSTemperature").checked;
        var Son = document.getElementById("ADSSon").checked;
        var Luminosite = document.getElementById("ADSLuminosite").checked;
        var CO2 = document.getElementById("ADSCO2").checked;
        var Humidite = document.getElementById("ADSHumidite").checked;

        console.log("c'est le resultat:");
        console.log(Salle);
        var url = "https://aip-confort.milebits.com:3001/ajouterSalle?token={token}";
        var data = {
            "Salle": Salle,
            "Temperature": Temperature,
            "Acoustique": Son,
            "Luminosite": Luminosite,
            "CO2": CO2,
            "Humidite": Humidite
        };
        console.log(data);
        var token = $('#token').val();
        console.log(token);

        $.ajax({
            url: "https://aip-confort.milebits.com:3001/ajouterSalle?token={token}".replace('{token}', token),
            type: "POST",
            dataType: "json",
            data: data,
            success: () => alert("C'est bon"),
            error: () => alert("C'est pas bon"),
            "headers": {"Access-Control-Allow-Origin": "*"}
        });
    }


    // A ajouter dans la page
    $('.status-sensor').on('submit', function () {
        var check = true;
        // ici etat capteur
        //collect token
        var token = $('#token').val();
        console.log(token);
        // Appel API
        $.ajax({
            url: "https://aip-confort.milebits.com:3001/Capteurs?token={token}".replace('{token}', token),
            type: "GET",
            crossDomain: true,
            success: function (resp) {
                var salles = resp['data'];
                var items = "";
                salles.forEach(function (salle, index) {
                    console.log(salle)
                    var nom = Object.keys(salle)[0];
                    var donnees = salle[nom][0];
                    var CO2 = donnees['CO2'];
                    var Humidite = donnees['Humidite'];
                    var Luminosite = donnees['Luminosite'];
                    var Son = donnees['Son'];
                    var Temperature = donnees['Temperature'];

                    var content = "Salle {NOM}".replace('{NOM}', nom);

                    var div = '<div style="text-align: center;" class="card"><div style="text-align: center;" class="card-header" id="Salle_{ID}_Heading"><h2 class="mb-0 text-center" style="text-align: center; width: 100%;"><button style="text-align: center;" class="btn btn-link btn-block text-left" type="button" data-toggle="collapse" data-target="#Salle_{ID}_Body" aria-expanded="false" aria-controls="Salle_{ID}_Body">{content} <div id="salle_rater_{ID}"></div></button></h2></div><div id="Salle_{ID}_Body" class="collapse" aria-labelledby="Salle_{ID}_Heading" data-parent="#DonneesClassementDiv"><div class="card-body"><div><strong>Temperature:</strong><span>{TEMPERATURE}</span></div><div><strong>Acoustique:</strong><span>{Acoustique}</span></div><div><strong>Humidite:</strong><span>{Humidite}</span></div><div><strong>Son:</strong><span>{Lum}</span></div><div><strong>CO2:</strong><span>{CO2}</span></div></div></div></div>';

                    div = div.replaceAll('{ID}', nom);
                    div = div.replaceAll('{content}', content);
                    div = div.replaceAll('{TEMPERATURE}', Temperature ? "Activé" : "Désactivé");
                    div = div.replaceAll('{Acoustique}', Son ? "Activé" : "Désactivé");
                    div = div.replaceAll('{Humidite}', Humidite ? "Activé" : "Désactivé");
                    div = div.replaceAll('{CO2}', CO2 ? "Activé" : "Désactivé");
                    div = div.replaceAll('{Lum}', Luminosite ? "Activé" : "Désactivé");
                    items += div;
                });

                $('#EtatsCapteursDiv').html(items);

            },
            error: function (resp) {
                console.log(resp);
                alert('Une erreur est survenu');
            }

        });

        return check;
    });

    var input5 = $('.validate-add-sensor .signup100');

    $('.form-add-sensor').on('submit', function () {
        var check = true;
        if (validate5(input5[1]) == false) {
            showValidate5(input5[1]);
            showValidate5(input5[0]);
            check = false;
        } else {
            // Récupérer données
            //    console.log("data")
            //    var salle = document.getElementById("ajouterCapteurSalle").value;
            //    var ip = document.getElementById("ADRip").value;
            //    var
            var salle = document.getElementById('ajouterCapteurSalle').value;
            var ip = document.getElementById('ADRip').value;
            var Temperature = document.getElementById("ADRTemperature").checked;
            var Son = document.getElementById("ADRSon").checked;
            var Luminosite = document.getElementById("ADRLuminosite").checked;
            var CO2 = document.getElementById("ADRCO2").checked;
            var Humidite = document.getElementById("ADRHumidite").checked;

            var data = {
                "Salle": salle,
                "ip": ip,
                "Temperature": Temperature,
                "Acoustique": Son,
                "Luminosite": Luminosite,
                "CO2": CO2,
                "Humidite": Humidite
            };
            var token = window.localStorage.getItem('token');
            // Ajouter ajouter capteur ici

            $.ajax({
                url: "https://aip-confort.milebits.com:3001/ajouterCapteurs?token={token}".replaceAll('{token}', token),
                type: "POST",
                dataType: "json",
                crossDomain: true,
                data: data,
                success: () => alert("Le capteur a bien été rajouté"),
                error: () => alert("Une erreur s'est produite !")
            });
        }

        return check;
    });

    function hideValidate5(input5) {
        var thisAlert = $(input5).parent();

        $(thisAlert).removeClass('alert-validate');
    }

    function showValidate5(input5) {
        var thisAlert = $(input5).parent();

        $(thisAlert).addClass('alert-validate');
    }

    function validate5(input5) {

        if ($(input5).attr('type') == 'ip' || $(input5).attr('name') == 'ip') {
            if ($(input5).val().trim().match(/^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/) == null) {
                return false;

            } else {

                var p1 = document.getElementById('ajouterCapteurSalle').value;
                if (p1.match(/^(S\d\d\d)$/) == null) {
                    return false;
                }
            }
        } else {
            var p1 = document.getElementById('ajouterCapteurSalle').value;
            if (p1.match(/^(S\d\d\d)$/) == null) {
                return false;
            }
        }
    }

    $('.form-add-sensor .signup100').each(function () {
        $(this).focus(function () {
            hideValidate(this);
        });
    });


    var input6 = $('.validate-delete-sensor .signup100');

    $('.form-delete-sensor').on('submit', function () {
        var check = true;
        for (var i = 0; i < input6.length; i++) {
            if (validate6(input6[i]) == false) {
                showValidate6(input6[i]);
                check = false;
            } else {
                // Récupérer données
                var input = $('#supprimer_raspberry_ip');
                var ipaddress = input.val();
                var token = window.localStorage.getItem('token');
                // Ajouter supprimer capteur ici
                $.ajax({
                    url: "https://aip-confort.milebits.com:3001/supprimerCapteurs?token={token}".replaceAll('{token}', token),
                    type: "POST",
                    data: {"ip": ipaddress},
                    dataType: "json",
                    crossDomain: true,
                    success: () => alert("Capteur supprimé"),
                    error: () => alert("Une erreur s'est produite !")
                });
            }
        }

        return check;
    });

    function hideValidate6(input6) {
        var thisAlert = $(input6).parent();

        $(thisAlert).removeClass('alert-validate');
    }

    function showValidate6(input6) {
        var thisAlert = $(input6).parent();

        $(thisAlert).addClass('alert-validate');
    }

    function validate6(input6) {

        if ($(input6).attr('type') == 'ip' || $(input6).attr('name') == 'ip') {
            if ($(input6).val().trim().match(/^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/) == null) {
                return false;
            } else {
            }
        } else {
            if ($(input6).val().trim() == '') {
                return false;
            }
        }
    }

    $('.form-delete-sensor .signup100').each(function () {
        $(this).focus(function () {
            hideValidate(this);
        });
    });


    var input7 = $('.validate-modify-sensor .signup100');

    $('.form-modify-sensor').on('submit', function () {
        var check = true;
        for (var i = 0; i < input7.length; i++) {
            if (validate7(input7[i]) == false) {
                showValidate7(input7[i]);
                check = false;
            } else {
                // Récupérer données
                var Salle = document.getElementById('MDRSalle').value;
                var Temperature = document.getElementById("MDRTemperature").checked;
                var Son = document.getElementById("MDRSon").checked;
                var Luminosite = document.getElementById("MDRLuminosite").checked;
                var CO2 = document.getElementById("MDRCO2").checked;
                var Humidite = document.getElementById("MDRHumidite").checked;

                var data = {
                    "Salle": Salle,
                    "Temperature": Temperature,
                    "Acoustique": Son,
                    "Luminosite": Luminosite,
                    "CO2": CO2,
                    "Humidite": Humidite
                };
                var token = window.localStorage.getItem('token');
                // Ajouter modifier capteur ici
                $.ajax({
                    url: "https://aip-confort.milebits.com:3001/modifierCapteurs?token={token}".replaceAll('{token}', token),
                    type: "POST",
                    dataType: "json",
                    crossDomain: true,
                    data: data,
                    success: () => alert("Etatscapteurs modifié"),
                    error: () => alert("Une erreur s'est produite")
                });
            }
        }

        return check;
    });

    function hideValidate7(input7) {
        var thisAlert = $(input7).parent();

        $(thisAlert).removeClass('alert-validate');
    }

    function showValidate7(input7) {
        var thisAlert = $(input7).parent();

        $(thisAlert).addClass('alert-validate');
    }

    function validate7(input7) {

        if ($(input7).attr('type') == 'ip' || $(input7).attr('name') == 'ip') {
            if ($(input7).val().trim().match(/^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/) == null) {
                return false;
            } else {

            }
        } else {
            if ($(input7).val().trim() == '') {

                return false;
            }
        }
    }

    $('.form-modify-sensor .signup100').each(function () {
        $(this).focus(function () {
            hideValidate(this);
        });
    });

    function validate_mdp() {
        var p1 = document.getElementById("Spsw").value;
        var p2 = document.getElementById("Spsw2").value;
        if (p1 != p2 || p1.length == 0) {
            return false;
        } else {
            return true;
        }
    }
})(jQuery);
