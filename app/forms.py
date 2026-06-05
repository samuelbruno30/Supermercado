from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo

class BuscaForm(FlaskForm):
    produtos = StringField('Lista de Produtos', validators=[
        DataRequired(message="A lista não pode estar vazia. Digite o que deseja buscar!"),
        Length(min=2, message="Digite pelo menos um produto válido.")
    ])
    submit = SubmitField('Pesquisar Preços')

class CadastroForm(FlaskForm):
    nome = StringField('Nome', validators=[
        DataRequired(message="O nome é obrigatório.")
    ])
    email = StringField('E-mail', validators=[
        DataRequired(message="O e-mail é obrigatório."),
        Email(message="Digite um e-mail válido.")
    ])
    senha = PasswordField('Senha', validators=[
        DataRequired(message="A senha é obrigatória."),
        Length(min=6, message="A senha deve ter pelo menos 6 caracteres.")
    ])
    confirmar_senha = PasswordField('Confirmar Senha', validators=[
        DataRequired(message="Confirme sua senha."),
        EqualTo('senha', message="As senhas precisam ser exatamente iguais.")
    ])
    submit = SubmitField('Criar Conta')

class LoginForm(FlaskForm):
    email = StringField('E-mail', validators=[
        DataRequired(message="O e-mail é obrigatório."),
        Email(message="Digite um e-mail válido.")
    ])
    senha = PasswordField('Senha', validators=[
        DataRequired(message="A senha é obrigatória.")
    ])
    submit = SubmitField('Entrar')