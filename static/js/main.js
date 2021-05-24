$(function(){

    //Form validation to prevent empty todos
    $('#todo-input, #update-todo-input').form({
    fields: {
      title: 'empty',
    },
  });

});