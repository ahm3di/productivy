# Productivy

A flask web application which allows users to manage projects and 
collaborate with others. Priority levels can be assigned to each task, using the
simple UI, allowing you to focus on the things that matter most.

# Setup

- Download or clone this repository:
`git clone https://github.com/ahm3di/productivy.git`

- Create a new virtual environment in the project directory:
`python3 -m venv venv`

- Activate the virtual environment:
    - Windows: `venv\scripts\activate`
    - Linux: `source venv/bin/activate`

- Install required dependencies to virtual environment:
`pip install -r requirements.txt`

- (Optional) Set your own `SECRET_KEY` in `config.py`
- Set environment variable `SETUP_CONFIG` to `config.Development`:
    - Windows: `set "CONFIG_SETUP=config.Development"`
    - Linux: `export CONFIG_STEUP="config.Development"`

- Create SQLite database for testing purposes:
`python3 create-db.py `

- Run the web application:
`flask run`

- View the live deployment at `http://127.0.0.1:5000/`

- Stop the application: <kbd>Ctrl</kbd> + <kbd>C</kbd>

- Deactivate the virtual environment: `deactivate`