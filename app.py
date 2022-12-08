import sys
import time
from flask import Flask, render_template, request, redirect, url_for, jsonify, Response
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, \
    logout_user, current_user
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Length, ValidationError, Email
from flask_wtf.file import FileField
from flask_bcrypt import Bcrypt
from datetime import datetime, timezone
import pytz
import os

UPLOAD_FOLDER = 'static/profile_images'
app = Flask(__name__)
env_config = os.environ['CONFIG_SETUP']
app.config.from_object(env_config)
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
csrf = CSRFProtect(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Used to convert UTC time to GMT and inject values in jinja2 template
@app.context_processor
def utility_processor():
    def utc_to_gmt(utc_dt):
        gmt = pytz.timezone("Europe/London")
        return utc_dt.replace(tzinfo=timezone.utc).astimezone(gmt)

    return dict(utc_to_gmt=utc_to_gmt)


def check_user_access(project_id):
    # Validate user access to a project to prevent users from altering
    # data they shouldn't have access to
    current_project = Project.query.filter_by(id=project_id).first()
    if not current_project:
        raise ValidationError("Project does not exist")
    if current_project in current_user.projects:
        return current_project
    else:
        raise ValidationError("You do not have access to this project")


def update_project_details(current_project):
    # Update project details with new information
    current_project.last_update = datetime.now(pytz.timezone("UTC"))
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
    password = db.Column(db.LargeBinary(80), nullable=False)
    projects = db.relationship('Project', secondary=user_project,
                               backref=db.backref('users'))


class Task(db.Model):
    # Define Task model
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable=False)
    complete = db.Column(db.BOOLEAN)
    priority = db.Column(db.Integer)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))


class Project(db.Model):
    # Define Project model
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), nullable=False)
    last_update = db.Column(db.TIMESTAMP, nullable=False)
    last_user = db.Column(db.Integer, nullable=False)
    tasks = db.relationship('Task', backref='project')


# SSE stream used to monitor changes to database and alert frontend
@app.route("/sse_stream/<int:project_id>")
@login_required
def sse_stream(project_id):
    current_project = check_user_access(project_id)
    last_update_time = current_project.last_update
    if current_project:
        def check_for_update():
            with app.app_context():
                current_update_time = last_update_time
                while last_update_time == current_update_time:
                    db.session.expire_all()
                    try:
                        current_update_time = Project.query.filter_by(id=project_id).first().last_update
                    except AttributeError:
                        yield f'data: {0}\n\n'
                    time.sleep(3)
            yield f'data: {1}\n\n'

        return Response(check_for_update(), mimetype='text/event-stream')


# Render updated task list
@app.route("/project_update", methods=["POST"])
@login_required
def project_update():
    project_id = request.form.get("value")
    current_project = check_user_access(project_id)

    if current_project:
        db.session.expire_all()
        task_list = Task.query.filter_by(project_id=project_id) \
            .order_by(Task.priority.desc(), Task.id.desc()).all()

    return render_template("task_list.html", task_list=task_list, project=current_project)


@app.route('/validate_user', methods=["POST"])
def validate_user():
    # Check to see if username or email exists in database
    existing_username = User.query.filter_by(
        username=request.form.get("value").lower()).first()

    existing_email = User.query.filter_by(
        email=request.form.get("value").lower()).first()

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
        # If neither email nor username are taken return any value
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


@app.route('/logout', methods=['GET'])
@login_required
def logout():
    # logout user
    logout_user()
    return redirect(url_for('login'))


@app.route('/')
@login_required
def index():
    # Query all projects for current user
    projects = Project.query.filter(Project.users.any(id=current_user.id)).all()
    users = User.query.all()
    return render_template('index.html', projects=projects, users=users)


@app.route('/project/<int:project_id>')
@login_required
def project(project_id):
    # Show all tasks from project
    current_project = check_user_access(project_id)
    # Get all tasks for selected project and sort by priority level
    task_list = Task.query.filter_by(project_id=project_id) \
        .order_by(Task.priority.desc(), Task.id.desc()).all()
    project_users = User.query.filter(User.projects.any(id=project_id)).all()
    return render_template('project.html', project=current_project,
                           task_list=task_list, users=project_users)


@app.route("/add_project", methods=["POST"])
@login_required
def add_project():
    # Add new project
    name = request.form.get("name")
    new_project = Project(name=name,
                          last_update=datetime.now(pytz.timezone("UTC")),
                          last_user=current_user.id)
    current_user.projects.append(new_project)
    db.session.add(new_project)
    db.session.commit()
    return redirect(url_for("index"))


@app.route("/delete_project/<int:project_id>", methods=["POST"])
@login_required
def delete_project(project_id):
    # Remove project
    current_project = check_user_access(project_id)
    project_tasks = Task.query.filter_by(project_id=project_id).all()
    for task in project_tasks:
        db.session.delete(task)
    db.session.delete(current_project)
    db.session.commit()
    return redirect(url_for("index"))


@app.route("/update_project/<int:project_id>", methods=["POST", "GET"])
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
        new_user = User.query.filter_by(
            email=request.form.get("name").lower()).first()
        if not new_user:
            new_user = User.query.filter_by(
                username=request.form.get("name").lower()) \
                .first()
        new_user.projects.append(current_project)
        db.session.commit()
        return redirect(url_for("project", project_id=project_id, ))


@app.route("/remove_user/<int:project_id>/<int:user_id>", methods=["POST"])
@login_required
def remove_user(project_id, user_id):
    # Remove user from project
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


@app.route("/add_task/<int:project_id>", methods=["POST"])
@login_required
def add_task(project_id):
    # Add new task
    current_project = check_user_access(project_id)
    title = request.form.get("title")
    priority = request.form.get("priority")
    # Set priority to high if no priority level is selected
    if priority == "":
        priority = 2
    new_task = Task(title=title, complete=False, priority=priority)
    update_project_details(current_project)
    current_project.tasks.append(new_task)
    db.session.add(new_task)
    db.session.commit()
    return redirect(url_for("project", project_id=current_project.id))


@app.route("/update_task_status/<int:project_id>/<int:task_id>", methods=["POST"])
@login_required
def update_task_status(project_id, task_id):
    # Update task status
    current_project = check_user_access(project_id)
    task = Task.query.filter_by(id=task_id).first()
    task.complete = not task.complete
    update_project_details(current_project)
    db.session.commit()
    return redirect(url_for("project", project_id=project_id))


@app.route("/update_task_priority/<int:project_id>/<int:task_id>/<int:priority>", methods=["POST"])
@login_required
def update_task_priority(project_id, task_id, priority):
    # Update task priority
    current_project = check_user_access(project_id)
    task = Task.query.filter_by(id=task_id).first()
    task.priority = priority
    update_project_details(current_project)
    db.session.commit()
    return redirect(url_for("project", project_id=project_id))


@app.route("/delete_task/<int:project_id>/<int:task_id>", methods=["POST"])
@login_required
def delete_task(project_id, task_id):
    # Delete task
    current_project = check_user_access(project_id)
    task = Task.query.filter_by(id=task_id).first()
    update_project_details(current_project)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for("project", project_id=project_id))


@app.route("/update_task/<int:project_id>/<int:task_id>", methods=["POST", "GET"])
@login_required
def update_task(project_id, task_id):
    # Update task
    current_project = check_user_access(project_id)
    task = Task.query.filter_by(id=task_id).first()
    if request.method == "POST":
        task.title = request.form.get("title")
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
