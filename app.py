from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, \
    logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Length, ValidationError, Email
from flask_wtf.file import FileField, FileAllowed
from flask_bcrypt import Bcrypt
from datetime import datetime
import os
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'static/profile_images'

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'secretkeygoeshere'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
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
        raise ValidationError("Project doesn't exist")
    if current_project in current_user.projects:
        return current_project
    else:
        raise ValidationError("You don't have access to this")


def update_project_details(current_project):
    # Update project details with new information
    current_project.last_update = datetime.now()
    current_project.last_user = current_user.id


class RegisterForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)])

    email = StringField(validators=[InputRequired(),
                                    Email(),
                                    Length(max=50)])
    password = PasswordField(
        validators=[InputRequired(), Length(min=4, max=20)])


class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(
        min=3, max=20)])

    password = PasswordField(validators=[InputRequired(), Length(
        min=4, max=20)])

    remember = BooleanField('remember me')


class UpdateAccountForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)])

    email = StringField(validators=[InputRequired(), Email(), Length(max=50)])
    image = FileField()
    password = PasswordField()


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
    image = db.Column(db.String(20), nullable=False, default='default.png')
    password = db.Column(db.String(80), nullable=False)
    projects = db.relationship('Project', secondary=user_project,
                               backref=db.backref('users'))


class Todo(db.Model):
    # Define Todo model
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable=False)
    complete = db.Column(db.BOOLEAN)
    priority = db.Column(db.Integer)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), nullable=False)
    last_update = db.Column(db.DATETIME, nullable=False)
    last_user = db.Column(db.Integer, nullable=False)
    todos = db.relationship('Todo', backref='project')


@app.route('/validate_user', methods=["POST"])
def validate_user():
    # Check to see if username or email exists in database
    existing_username = User.query.filter_by(
        username=request.form.get("value")).first()

    existing_email = User.query.filter_by(
        email=request.form.get("value")).first()

    # Validation when user attempts to update account details
    if request.form.get("identifier") == "updateDetails":
        # Check if username is already taken by anyone, but the current user
        if existing_username and \
                existing_username.username != current_user.username:
            return jsonify("2")

        # Check if email is already taken by anyone, but the current user
        elif existing_email and \
                existing_email.email != current_user.email:
            return jsonify("3")
        # If neither email or username are taken return any value
        else:
            return jsonify("4")

    # Validation for user registration
    elif existing_username:
        return jsonify("0")
    elif existing_email:
        return jsonify("1")
    else:
        return jsonify("4")


@app.route('/register', methods=['GET', 'POST'])
def register():
    # Register user
    if current_user.is_authenticated:
        return redirect(url_for('/'))

    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(username=form.username.data.lower(),
                        email=form.email.data.lower(), password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    # Login user
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data.lower()).first()
        if not user:
            user = User.query.filter_by(email=form.username.data.lower()). \
                first()

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
    users = User.query.all()
    image = url_for('static', filename='profile_images/' + current_user.image)
    return render_template('index.html', projects=projects, users=users,
                           image=image)


@app.route('/project/<int:project_id>')
@login_required
def project(project_id):
    # Show all todos from project
    current_project = check_user_access(project_id)
    # Get all todos for selected project and sort by priority level
    todo_list = Todo.query.filter_by(project_id=project_id) \
        .order_by(Todo.priority.desc(), Todo.id.desc()).all()
    project_users = User.query.filter(User.projects.any(id=project_id)).all()
    return render_template('project.html', project=current_project,
                           todo_list=todo_list, users=project_users)


@app.route("/add_project", methods=["POST"])
@login_required
def add_project():
    # Add new project
    name = request.form.get("name")
    new_project = Project(name=name, last_update=datetime.now(),
                          last_user=current_user.id)
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
        update_project_details(current_project)
        db.session.commit()
        return redirect(url_for("project", project_id=project_id))


@app.route("/add_user/<int:project_id>", methods=["POST", "GET"])
@login_required
def add_user(project_id):
    # Add user to project
    current_project = check_user_access(project_id)
    if request.method == "POST":
        new_user = User.query.filter_by(email=request.form.get("name")).first()
        if not new_user:
            new_user = User.query.filter_by(username=request.form.get("name")) \
                .first()
        new_user.projects.append(current_project)
        db.session.commit()
        return redirect(url_for("project", project_id=project_id, ))


@app.route("/delete_user/<int:project_id>/<int:user_id>")
@login_required
def delete_user(project_id, user_id):
    # Delete user from project
    current_project = check_user_access(project_id)
    user = User.query.filter_by(id=user_id).first()
    update_project_details(current_project)
    user.projects.remove(current_project)
    remaining_users = User.query.filter(User.projects.any(id=project_id)).all()
    if not remaining_users:
        db.session.delete(current_project)
    db.session.commit()
    if user_id != current_user.id:
        return redirect(url_for("project", project_id=project_id))
    return redirect(url_for("index"))


@app.route("/add_todo/<int:project_id>", methods=["POST"])
@login_required
def add_todo(project_id):
    # Add new todo
    current_project = check_user_access(project_id)
    title = request.form.get("title")
    priority = request.form.get("priority")
    new_todo = Todo(title=title, complete=False, priority=priority)
    update_project_details(current_project)
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
    update_project_details(current_project)
    db.session.commit()
    return redirect(url_for("project", project_id=project_id))


@app.route(
    "/update_todo_priority/<int:project_id>/<int:todo_id>/<int:priority>")
@login_required
def update_todo_priority(project_id, todo_id, priority):
    # Update todo priority
    current_project = check_user_access(project_id)
    todo = Todo.query.filter_by(id=todo_id).first()
    todo.priority = priority
    update_project_details(current_project)
    db.session.commit()
    return redirect(url_for("project", project_id=project_id))


@app.route("/delete_todo/<int:project_id>/<int:todo_id>")
@login_required
def delete_todo(project_id, todo_id):
    # Delete todo
    current_project = check_user_access(project_id)
    todo = Todo.query.filter_by(id=todo_id).first()
    update_project_details(current_project)
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
        update_project_details(current_project)
        db.session.commit()
        return redirect(url_for("project", project_id=project_id))


@app.route('/profile', methods=["POST", "GET"])
@login_required
def profile():
    # Show user profile
    image = url_for('static', filename='profile_images/' + current_user.image)
    form = UpdateAccountForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        if form.password.data:
            current_user.password = bcrypt.generate_password_hash(
                form.password.data)
        image = request.files['image']
        if image:
            filename, file_extension = os.path.splitext(image.filename)
            filename = str(current_user.id) + file_extension
            if current_user.image != "default.png":
                os.remove(app.config["UPLOAD_FOLDER"] + "/" +
                          str(current_user.image))
            image.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            current_user.image = filename
        db.session.commit()
        return redirect(url_for('profile'))
    return render_template('profile.html', user=current_user, image=image,
                           form=form)
