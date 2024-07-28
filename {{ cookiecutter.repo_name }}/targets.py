from invoke import task
import os
import shutil

PROJECT_NAME = "{{ cookiecutter.repo_name }}"
PYTHON_VERSION = "{{ cookiecutter.python_version_number }}"
PYTHON_INTERPRETER = "python"
MODULE_NAME = "{{ cookiecutter.module_name }}"

@task
def requirements(ctx):
    """Install Python Dependencies"""
    dependency_file = "{{ cookiecutter.dependency_file }}"
    if dependency_file == "requirements.txt":
        ctx.run(f"{PYTHON_INTERPRETER} -m pip install -U pip")
        ctx.run(f"{PYTHON_INTERPRETER} -m pip install -r requirements.txt")
    elif dependency_file == "environment.yml":
        ctx.run(f"conda env update --name {PROJECT_NAME} --file environment.yml --prune")
    elif dependency_file == "Pipfile":
        ctx.run("pipenv install")

@task
def clean(ctx):
    """Delete all compiled Python files"""
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith(".pyc") or file.endswith(".pyo"):
                os.remove(os.path.join(root, file))
        for dir in dirs:
            if dir == "__pycache__":
                shutil.rmtree(os.path.join(root, dir))

@task
def lint(ctx):
    """Lint using flake8 and black (use `invoke format` to do formatting)"""
    ctx.run(f"flake8 {MODULE_NAME}")
    ctx.run(f"isort --check --diff --profile black {MODULE_NAME}")
    ctx.run(f"black --check --config pyproject.toml {MODULE_NAME}")

@task
def format(ctx):
    """Format source code with black"""
    ctx.run(f"black --config pyproject.toml {MODULE_NAME}")

@task
def sync_data_down(ctx):
    """Download Data from storage system"""
    storage_system = "{{ cookiecutter.dataset_storage }}"
    if storage_system == "s3":
        bucket = "{{ cookiecutter.dataset_storage.s3.bucket }}"
        profile = "{{ cookiecutter.dataset_storage.s3.aws_profile }}"
        profile_option = f" --profile {profile}" if profile != "default" else ""
        ctx.run(f"aws s3 sync s3://{bucket}/data/ data/{profile_option}")
    elif storage_system == "azure":
        container = "{{ cookiecutter.dataset_storage.azure.container }}"
        ctx.run(f"az storage blob download-batch -s {container}/data/ -d data/")
    elif storage_system == "gcs":
        bucket = "{{ cookiecutter.dataset_storage.gcs.bucket }}"
        ctx.run(f"gsutil -m rsync -r gs://{bucket}/data/ data/")

@task
def sync_data_up(ctx):
    """Upload Data to storage system"""
    storage_system = "{{ cookiecutter.dataset_storage }}"
    if storage_system == "s3":
        bucket = "{{ cookiecutter.dataset_storage.s3.bucket }}"
        profile = "{{ cookiecutter.dataset_storage.s3.aws_profile }}"
        profile_option = f" --profile {profile}" if profile != "default" else ""
        ctx.run(f"aws s3 sync data/ s3://{bucket}/data{profile_option}")
    elif storage_system == "azure":
        container = "{{ cookiecutter.dataset_storage.azure.container }}"
        ctx.run(f"az storage blob upload-batch -d {container}/data/ -s data/")
    elif storage_system == "gcs":
        bucket = "{{ cookiecutter.dataset_storage.gcs.bucket }}"
        ctx.run(f"gsutil -m rsync -r data/ gs://{bucket}/data/")

@task
def create_environment(ctx):
    """Set up python interpreter environment"""
    environment_manager = "{{ cookiecutter.environment_manager }}"
    dependency_file = "{{ cookiecutter.dependency_file }}"
    if environment_manager == "conda":
        if dependency_file != "environment.yml":
            ctx.run(f"conda create --name {PROJECT_NAME} python={PYTHON_VERSION} -y")
        else:
            ctx.run(f"conda env create --name {PROJECT_NAME} -f environment.yml")
        print(f">>> conda env created. Activate with:\nconda activate {PROJECT_NAME}")
    elif environment_manager == "virtualenv":
        ctx.run(f"virtualenv {PROJECT_NAME} --python={PYTHON_INTERPRETER}")
        print(f">>> New virtualenv created. Activate with:\nsource {PROJECT_NAME}/bin/activate")
    elif environment_manager == "pipenv":
        ctx.run(f"pipenv --python {PYTHON_VERSION}")
        print(f">>> New pipenv created. Activate with:\npipenv shell")

@task
def data(ctx):
    """Make Dataset"""
    requirements(ctx)
    ctx.run(f"{PYTHON_INTERPRETER} {MODULE_NAME}/dataset.py")

@task
def help(ctx):
    """Display help message"""
    print("Available tasks:")
    for task in ctx.collection:
        print(f"{task.name}: {task.help}")

# Aliases for some common tasks
ns = Collection()
ns.add_task(requirements)
ns.add_task(clean)
ns.add_task(lint)
ns.add_task(format)
ns.add_task(sync_data_down)
ns.add_task(sync_data_up)
ns.add_task(create_environment)
ns.add_task(data)
ns.add_task(help)
