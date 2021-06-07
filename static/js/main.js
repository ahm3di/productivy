$(function () {
    // Custom fomantic rule to check if username is already registered
    $.fn.form.settings.rules.checkUsername = function (value) {
        let res = true
        $.ajax({
            url: '/validate_user',
            type: "POST",
            async: false,
            data: {
                username: value
            },
            dataType: 'json',
            success: function (data) {
                console.log(data);
                if (data == "0") {
                    res = false;
                } else {
                    res = true;
                }
            }
        });
        return res;
    };

    // Custom fomantic rule to check if email is already registered
    $.fn.form.settings.rules.checkEmail = function (value) {
        let res = true
        $.ajax({
            url: '/validate_user',
            type: "POST",
            async: false,
            data: {
                email: value
            },
            dataType: 'json',
            success: function (data) {
                console.log(data);
                if (data == "1") {
                    res = false;
                } else {
                    res = true;
                }
            }
        });
        return res;
    };


//Form validation to prevent empty project and todo names
    $('#todo-input, #update-todo-form, #project-input, #update-project-input')
        .form({
            fields: {
                title: 'empty',
                name: 'empty'
            },
        });

    $('#register-form, #login-form')
        .form({
            fields: {
                username: {
                    identifier: 'username',
                    rules: [
                        {
                            type: 'empty',
                            prompt: 'Please enter your username',

                            type: 'length[3]',
                            prompt: 'Your username must be at least 3 characters',

                            type: 'checkUsername',
                            prompt: 'Username already exists'
                        }
                    ]
                },
                email: {
                    identifier: 'email',
                    rules: [
                        {
                            type: 'empty',
                            prompt: 'Please enter your email',

                            type: 'email',
                            prompt: 'Please enter a valid email address',

                            type: 'checkEmail',
                            prompt: 'Email already exists'
                        }
                    ]
                },
                password: {
                    identifier: 'password',
                    rules: [
                        {
                            type: 'empty',
                            prompt: 'Please enter your password'
                        },
                        {
                            type: 'length[4]',
                            prompt: 'Your password must be at least 4 characters'
                        }
                    ]
                }
            }
        });

    $('#login-form')
        .form({
            fields: {
                username: {
                    identifier: 'username',
                    rules: [
                        {
                            type: 'empty',
                            prompt: 'Please enter your username',

                            type: 'length[3]',
                            prompt: 'Your username must be at least 3 characters',
                        }
                    ]
                },
                email: {
                    identifier: 'email',
                    rules: [
                        {
                            type: 'empty',
                            prompt: 'Please enter your email',

                            type: 'email',
                            prompt: 'Please enter a valid email address',
                        }
                    ]
                },
                password: {
                    identifier: 'password',
                    rules: [
                        {
                            type: 'empty',
                            prompt: 'Please enter your password'
                        },
                        {
                            type: 'length[4]',
                            prompt: 'Your password must be at least 4 characters'
                        }
                    ]
                }
            }
        });

    $('.button').popup();

    $('.ui.dropdown').dropdown();

    $('.update-project-button').on('click', function () {
        $('#update-project-modal').modal('show');
    });

    $('.add-user-button').on('click', function () {
        $('#add-users-modal').modal('show');
    });

    $('.update-todo-button').on('click', function () {
        // Get todo title and id from hidden fields
        var current_todo_id = $('.current-todo-id').val();
        var current_todo_title = $('.current-todo-title').val();

        // Set modal input placeholder to todo title
        $('#update-todo-modal #update-todo-input').val(current_todo_title)

        // Get form action url
        var action = $('#update-todo-modal #update-todo-form').attr("action");

        // Append todo title to form action url
        $('#update-todo-modal #update-todo-form').attr('action',
            action + current_todo_id);

        //Display modal
        $('#update-todo-modal').modal('show')
    });
});