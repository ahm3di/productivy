from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    complete = db.Column(db.BOOLEAN)


@app.route('/')
def index():
    # Show all todos
    todo_list = Todo.query.all()
    return render_template('index.html', todo_list=todo_list)


@app.route("/add", methods=["POST"])
def add():
    # Add new todo
    title = request.form.get("title")
    new_todo = Todo(title=title, complete=False)
    db.session.add(new_todo)
    db.session.commit()
    return redirect(url_for("index"))


@app.route("/update_status/<int:todo_id>")
def update_status(todo_id):
    # Update todo status
    todo = Todo.query.filter_by(id=todo_id).first()
    todo.complete = not todo.complete
    db.session.commit()
    return redirect(url_for("index"))


@app.route("/delete/<int:todo_id>")
def delete(todo_id):
    # Delete todo
    todo = Todo.query.filter_by(id=todo_id).first()
    db.session.delete(todo)
    db.session.commit()
    return redirect(url_for("index"))


@app.route("/update/<int:todo_id>", methods=["POST", "GET"])
def update(todo_id):
    # Update todo
    todo = Todo.query.filter_by(id=todo_id).first()

    if request.method == "POST":
        todo.title = request.form.get("title")
        db.session.commit()
        return redirect("/")
    else:
        return render_template('update.html', todo=todo)
