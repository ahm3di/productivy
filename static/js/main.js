$(function () {
    // Custom fomantic rule to check if username is already registered
    $.fn.form.settings.rules.checkUser = function (value, formIdentifier) {
        let result = true
        $.ajax({
            url: '/validate_user',
            type: "POST",
            async: false,
            data: {
                value: value,
            },
            dataType: 'json',
            success: function (data) {
                console.log(data);
                // If username or email exist in database and error is displayed
                if (data == "0" && formIdentifier == "username") {
                    result = false;
                } else if (data == "1" && formIdentifier == "email") {
                    result = false;
                }
                // Error displayed if username or email don't exist
                else if (data == "4" && formIdentifier == "userEmail") {
                    result = false;
                } else {
                    result = true;
                }
            }
        });
        return result;
    };

    // Custom fomantic rule for updating user details
    $.fn.form.settings.rules.updateDetails = function (value, formIdentifier) {
        let result = true
        $.ajax({
            url: '/validate_user',
            type: "POST",
            async: false,
            data: {
                value: value,
                identifier: "updateDetails"
            },
            dataType: 'json',
            success: function (data) {
                console.log(data);
                // Error displayed if username or email are already taken
                if (data == "2" && formIdentifier == "username") {
                    result = false;
                } else if (data == "3" && formIdentifier == "email") {
                    result = false;
                } else {
                    result = true;
                }
            }
        });
        return result;
    };

    // Form validation to prevent empty project and todo names
    $('#todo-form, #update-todo-form, #update-project-form')
        .form({
            fields: {
                title: 'empty',
                name: 'empty'
            },
        });

    // Form validation for register form
    $('#register-form')
        .form({
            fields: {
                username: {
                    identifier: 'username',
                    rules: [
                        {
                            type: 'empty',
                            prompt: 'Please enter a username',
                        },
                        {
                            type: 'length[3]',
                            prompt: 'Your username must be at least 3 characters',
                        },
                        {
                            type: 'checkUser[username]',
                            prompt: 'Username already exists'
                        },
                        {
                            type: 'regExp[/^\\w+$/]',
                            prompt: 'Username can only contain letters, ' +
                                'numbers or underscore '
                        }
                    ]
                },
                email: {
                    identifier: 'email',
                    rules: [
                        {
                            type: 'empty',
                            prompt: 'Please enter your email',
                        },
                        {
                            type: 'email',
                            prompt: 'Please enter a valid email address',
                        },
                        {
                            type: 'checkUser[email]',
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

    // Form validation for login form
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
                        },
                        {
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

    // Form validation to prevent empty project and todo names
    $('#add-users-form')
        .form({
            fields: {
                name: {
                    identifier: 'name',
                    rules: [
                        {
                            type: 'checkUser[userEmail]',
                            prompt: "Please enter a valid username/email"
                        },
                    ]
                }
            },
        });

    // Form validation for login form
    $('#update-user-form')
        .form({
            fields: {
                username: {
                    identifier: 'username',
                    rules: [
                        {
                            type: 'updateDetails[username]',
                            prompt: 'Username already exists, ' +
                                'please try a different one',
                        },
                        {
                            type: 'length[3]',
                            prompt: 'Your username must be at least 3 characters',
                        }
                    ]
                },
                email: {
                    identifier: 'email',
                    rules: [
                        {
                            type: 'updateDetails[email]',
                            prompt: 'Email already exists, ' +
                                'please enter another email',
                        },
                        {
                            type: 'email',
                            prompt: 'Please enter a valid email address',
                        }
                    ]
                },
                password: {
                    identifier: 'password',
                    rules: [
                        {
                            type: 'regExp[/^(\\S{4,})?$/]',
                            prompt: 'Your new password must be at ' +
                                'least 4 characters'
                        }
                    ]
                }
            }
        });


    $('.update-todo-button, .delete-todo-button').popup();

    $('.ui.dropdown').dropdown();

    $('.update-project-button').on('click', function () {
        $('#update-project-modal').modal('show');
    });

    $('.manage-users-button').on('click', function () {
        $('#manage-users-modal').modal('show');
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

    $('#update-user-button').on('click', function () {
        $('#update-user-modal').modal('show');
    });
});