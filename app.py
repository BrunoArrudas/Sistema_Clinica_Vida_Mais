from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Configuração do banco SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///clinica.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Modelo Paciente
class Paciente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    idade = db.Column(db.Integer, nullable=False)
    telefone = db.Column(db.String(20), nullable=False)

# Rota inicial (lista pacientes)
@app.route('/')
def index():
    pacientes = Paciente.query.all()
    return render_template('index.html', pacientes=pacientes)

# Rota de cadastro
@app.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar():
    if request.method == 'POST':
        nome = request.form['nome']
        idade = request.form['idade']
        telefone = request.form['telefone']

        novo_paciente = Paciente(nome=nome, idade=idade, telefone=telefone)
        db.session.add(novo_paciente)
        db.session.commit()

        return redirect(url_for('index'))

    return render_template('cadastrar.html')

# Rota de edição
@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    paciente = Paciente.query.get_or_404(id)
    if request.method == 'POST':
        paciente.nome = request.form['nome']
        paciente.idade = request.form['idade']
        paciente.telefone = request.form['telefone']
        db.session.commit()
        return redirect(url_for('index'))

    return render_template('editar.html', paciente=paciente)

# Rota de exclusão
@app.route('/excluir/<int:id>')
def excluir(id):
    paciente = Paciente.query.get_or_404(id)
    db.session.delete(paciente)
    db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Cria as tabelas no banco
    app.run(debug=True)
