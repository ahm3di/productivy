$(function(){

    //Form validation to prevent empty todos
    $('#todo-input').form({
    fields: {
      title: 'empty',
    },
  });

});