import click
from flask import current_app
from db import db
from models import *

def init_app(app):
    
    @app.cli.command("create-db")
    def create_db():
        import models
        db.create_all()
        click.echo("Banco de dados criado com sucesso!")

    @app.cli.command("drop-db")
    @click.confirmation_option(prompt="Tem certeza que deseja remover o banco de dados? Esta ação é irreversível.")
    def drop_db():
        import models
        db.drop_all()
        click.echo("Banco de dados removido com sucesso!")

    @app.cli.command("seed-db")
    def seed_db():
        click.echo("Isso ira popular o banco com dados de teste. Deseja continuar? [y/N]: ", nl=False)

        confirm = input().strip().lower()

        if confirm not in ("y", "yes", "s", "sim"):
            click.echo("Operacao cancelada.")
            return

        try:
            click.echo("Iniciando Seed de Desenvolvimento...")

            maria = User(
                name="Maria",
                senha="ma123",
                email="maria@email.com"
            )
            db.session.add(maria)
            db.session.commit()

            pedro = User(
                name="Pedro",
                senha="pe123",
                email="pedro@email.com"
            )
            db.session.add(pedro)
            db.session.commit()

        except Exception as e:
            db.session.rollback()
            click.echo(f"Erro catastrófico no seed: {e}")