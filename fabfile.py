# coding=utf-8
from fabric.colors import green
from fabric.context_managers import cd
from fabric.operations import run
from fabric.state import env

env.shell = "/bin/zsh -c"

APP_NAME = "mittag"

env.path = f"/opt/www/{APP_NAME}"
env.hosts = ["mamasystems.de"]


# T A S K S
# ###########
def deploy_only():
    """Pull all updates from the remote repository."""
    with cd(env.path):
        print(green("updating from repository .."))
        run("git pull")


def clear_cache():
    with cd(env.path):
        print(green("\ndeleting cache .."))
        manage("clear_cache")


def restart():
    """Restart nginx and the backend worker."""
    print(green("\nrestarting server .."))
    run(f"pm2 restart {APP_NAME}")

    clear_cache()


def deploy():
    deploy_only()
    update_static()

    restart()


def migrate():
    """
    Pull all updates from the remote repository.
    Migrates the database and installs new lib versions from requirements.
    Static files are also collected.
    """
    deploy_only()

    with cd(env.path):
        print(green("updating packages .."))
        # this might cause some trouble: https://github.com/python-poetry/poetry/issues/732
        run("python --version")
        run("poetry run pip install --upgrade pip setuptools")
        run("poetry install")

        print(green("migrating database .."))
        manage("migrate --noinput")

        update_static()

        build_frontend()

    restart()


def update_static():
    with cd(env.path):
        print(green("compressing files .."))
        manage("compilescss")
        # manage("compress -e pug,html --force")

        print(green("collecting static files .."))
        manage("collectstatic --noinput")


def manage(command):
    run("poetry run ./manage.py " + command)


def build_frontend():
    with cd(env.path):
        with cd("speisekarte"):
            run("yarn build")
