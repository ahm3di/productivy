$(function () {
    // Load jQuery animations
    activateAnimations()

    var csrf_token = $('input[name=csrf-token]').attr('content')
    var project_id = $('input[name=project_id]').attr('content')

    // Open WebSocket to get updates when user is on project page
    if (project_id) {

        var socket = io();

        // Join socketIO room for current project
        socket.emit('join', project_id)

        // Ping client every 30 seconds to keep connection alive
        setInterval(function () {
            socket.emit('ping')
        }, 30000)

        // Request updated project data on socket message
        socket.on('update', function (data) {
            $.ajax({
                url: '/project_update',
                type: "POST",
                async: true,
                headers: {
                    "X-CSRFToken": csrf_token,
                },
                data: {
                    value: project_id,
                },
                success: function (data) {
                    // Replace existing task list with updated list
                    document.getElementById("task-list").innerHTML = data
                    // Reload jQuery animations after tasks are updated
                    activateAnimations()
                }
            });
        });
    }

    // Custom fomantic rule to check if username is already registered
    $.fn.form.settings.rules.checkUser = function (value, formIdentifier) {
        let result = true
        $.ajax({
            url: '/validate_user',
            type: "POST",
            async: false,
            headers: {
                "X-CSRFToken": csrf_token,
            },
            data: {
                value: value,
            },
            dataType: 'json',
            success: function (data) {
                // If username or email exist in database an error is displayed
                if (data === "0" && formIdentifier === "username") {
                    result = false;
                } else if (data === "1" && formIdentifier === "email") {
                    result = false;
                }
                // Error displayed if username or email don't exist
                else result = !(data === "4" && formIdentifier === "userEmail");
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
            headers: {
                "X-CSRFToken": csrf_token,
            },
            data: {
                value: value,
                identifier: "updateDetails"
            },
            dataType: 'json',
            success: function (data) {
                // Error displayed if username or email are already taken
                if (data === "2" && formIdentifier === "username") {
                    result = false;
                } else result = !(data === "3" && formIdentifier === "email");
            }
        });
        return result;
    };

    // Form validation to prevent empty project and task names
    $('#task-form, #update-task-form, #update-project-form')
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

    // Form validation to prevent empty project and task names
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

    function activateAnimations() {
        $('.update-task-button, .delete-task-button-button, .priority-indicator, .remove-user-button').popup();

        $('.ui.dropdown').dropdown();

        $('.selection.dropdown').dropdown();

        $('.update-project-button').on('click', function () {
            $('#update-project-modal').modal('show');

            $('#update-project-cancel').on('click', function () {
                $('#update-project-modal').modal('hide');
            });
        });

        $('.manage-users-button').on('click', function () {
            $('#manage-users-modal').modal('show');

            $('#manage-users-cancel').on('click', function () {
                $('#manage-users-modal').modal('hide');
            });
        });

        $('.delete-project-button').on('click', function () {
            $('#delete-project-modal').modal('show');
        });

        $('.update-task-button').on('click', function () {
            // Get task title and id
            let current_task_id = $(this).attr('data-task-id')
            let current_task_title = $(this).attr('data-task-title')

            // Set modal input placeholder to task title
            $('#update-task-modal #update-task-input').val(current_task_title)

            // Get form action url
            const action = $('#update-task-form').attr("action");

            // Append task id to form action url
            $('#update-task-form').attr('action',
                action + current_task_id);

            // Display modal
            $('#update-task-modal').modal('show')

            // Hide modal on cancel
            $('#task-modal-cancel').on('click', function () {
                $('#update-task-modal').modal('hide');
            });
        });

        $('#update-user-button').on('click', function () {
            $('#update-user-modal').modal('show');

            // Hide modal on cancel
            $('#update-user-cancel').on('click', function () {
                $('#update-user-modal').modal('hide');
            });
        });

        $('.task-dropdown').dropdown({
            'onChange': function (value, text, $selectedItem) {
                const action = $('.update-priority-form').attr("action")
                $('.update-priority-form').attr('action',
                    action + value);
                $(".update-priority-form").submit();
            }
        });
        $("#project-settings-dropdown").dropdown({
            action: 'nothing',
            action: 'hide'
        })

    }
});
