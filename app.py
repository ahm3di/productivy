﻿from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, \
    logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Length, ValidationError, Email
from flask_bcrypt import Bcrypt
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'secretkeygoeshere'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def check_user_access(project_id):
    # Validate user access to a project to prevent users from altering
    # data they shouldn't have access to
    current_project = Project.query.filter_by(id=project_id).first()
    if not current_project:
        raise ValidationError("Project doesn't exist (maybe a")
    if current_project in current_user.projects:
        return current_project
    else:
        raise ValidationError("You don't have access to this")


def validate_user(username, email):
    # Check to see if username or email already exists
    existing_username = User.query.filter_by(
        username=username).first()

    existing_email = User.query.filter_by(
        email=email).first()

    if existing_email or existing_username:
        raise ValidationError("User already exists")


class RegisterForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)])

    email = StringField(validators=[InputRequired(),
                                    Email(message='Invalid email'),
                                    Length(max=50)])

    password = PasswordField(
        validators=[InputRequired(), Length(min=4, max=20)])


class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(
        min=3, max=20)])

    password = PasswordField(validators=[InputRequired(), Length(
        min=4, max=20)])

    remember = BooleanField('remember me')


# Association table between User and Project
user_project = db.Table('user_project',
                        db.Column('user_id', db.Integer,
                                  db.ForeignKey('user.id')),

                        db.Column('project_id', db.Integer,
                                  db.ForeignKey('project.id'))
                        )


class User(db.Model, UserMixin):
    # Define User model
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    email = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)
    projects = db.relationship('Project', secondary=user_project,
                               backref=db.backref('users'))


class Todo(db.Model):
    # Define Todo model
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable=False)
    complete = db.Column(db.BOOLEAN)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), nullable=False)
    last_update = db.Column(db.DATETIME, nullable=False)
    todos = db.relationship('Todo', backref='project')


@app.route('/register', methods=['GET', 'POST'])
def register():
    # Register user
    form = RegisterForm()
    if form.validate_on_submit():
        validate_user(form.username.data, form.email.data)
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(username=form.username.data,
                        email=form.email.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    # Login user
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.username.data).first()
        if not user:
            user = User.query.filter_by(username=form.username.data).first()

        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember.data)
                return redirect(url_for('index'))
    return render_template('login.html', form=form)


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    # logout user
    logout_user()
    return redirect(url_for('login'))


@app.route('/')
@login_required
def index():
    # Show all projects for current user
    projects = Project.query.filter(Project.users.any(id=current_user.id)).all()
    return render_template('index.html', projects=projects)


@app.route('/project/<int:project_id>')
@login_required
def project(project_id):
    # Show all todos from project
    current_project = check_user_access(project_id)
    todo_list = Todo.query.filter_by(project_id=project_id).all()
    return render_template('project.html', project=current_project,
                           todo_list=todo_list)


@app.route("/add_project", methods=["POST"])
@login_required
def add_project():
    # Add new project
    name = request.form.get("name")
    new_project = Project(name=name, last_update=datetime.now())
    current_user.projects.append(new_project)
    db.session.add(new_project)
    db.session.commit()
    return redirect(url_for("index"))


@app.route("/delete_project/<int:project_id>")
@login_required
def delete_project(project_id):
    # Remove project
    current_project = check_user_access(project_id)
    project_todos = Todo.query.filter_by(project_id=project_id).all()
    for todo in project_todos:
        db.session.delete(todo)
    db.session.delete(current_project)
    db.session.commit()
    return redirect(url_for("index"))


@app.route("/update_project/<int:project_id>",
           methods=["POST", "GET"])
@login_required
def update_project(project_id):
    # Update project name
    current_project = check_user_access(project_id)
    if request.method == "POST":
        current_project.name = request.form.get("name")
        current_project.last_update = datetime.now()
        db.session.commit()
        return redirect(url_for("project", project_id=project_id))
    else:
        return render_template('update-project.html', project=current_project)


@app.route("/add_user/<int:project_id>", methods=["POST", "GET"])
@login_required
def add_user(project_id):
    # Add user to project
    current_project = check_user_access(project_id)
    if request.method == "POST":
        new_user = User.query.filter_by(email=request.form.get("name")).first()
        if not new_user:
            new_user = User.query.filter_by(username=request.form.get("name"))\
                .first()
        new_user.projects.append(current_project)
        db.session.commit()
        return redirect(url_for("project", project_id=project_id))

    else:
        return render_template('add-user.html', project_id=project_id)


@app.route("/add_todo/<int:project_id>", methods=["POST"])
@login_required
def add_todo(project_id):
    # Add new todo
    current_project = check_user_access(project_id)
    title = request.form.get("title")
    new_todo = Todo(title=title, complete=False)
    current_project.last_update = datetime.now()
    current_project.todos.append(new_todo)
    db.session.add(new_todo)
    db.session.commit()
    return redirect(url_for("project", project_id=current_project.id))


@app.route("/update_todo_status/<int:project_id>/<int:todo_id>")
@login_required
def update_todo_status(project_id, todo_id):
    # Update todo status
    current_project = check_user_access(project_id)
    todo = Todo.query.filter_by(id=todo_id).first()
    todo.complete = not todo.complete
    current_project.last_update = datetime.now()
    db.session.commit()
    return redirect(url_for("project", project_id=project_id))


@app.route("/delete_todo/<int:project_id>/<int:todo_id>")
@login_required
def delete_todo(project_id, todo_id):
    # Delete todo
    current_project = check_user_access(project_id)
    todo = Todo.query.filter_by(id=todo_id).first()
    current_project.last_update = datetime.now()
    db.session.delete(todo)
    db.session.commit()
    return redirect(url_for("project", project_id=project_id))


@app.route("/update_todo/<int:project_id>/<int:todo_id>",
           methods=["POST", "GET"])
@login_required
def update_todo(project_id, todo_id):
    # Update todo
    current_project = check_user_access(project_id)
    todo = Todo.query.filter_by(id=todo_id).first()

    if request.method == "POST":
        todo.title = request.form.get("title")
        current_project.last_update = datetime.now()
        db.session.commit()
        return redirect(url_for("project", project_id=project_id))
    else:
        return render_template('update-todo.html', project_id=project_id, todo=todo)
