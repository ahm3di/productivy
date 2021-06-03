$(function () {

    //Form validation to prevent empty project and todo names
    $('#todo-input, #update-todo-input, #project-input, #update-project-input').form({
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
                            prompt: 'Your username must be at least 3 characters'
                        }
                    ]
                },
                email:{
                    identifier: 'email',
                    rules: [
                        {
                            type: 'empty',
                            prompt: 'Please enter your email',

                            type: 'email',
                            prompt: 'Please enter a valid email address'
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

});