from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import func

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///clinica.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Paciente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    idade = db.Column(db.Integer, nullable=False)
    telefone = db.Column(db.String(20), nullable=False)
    rg = db.Column(db.String(20))
    cpf = db.Column(db.String(20))
    pagamentos_em_dia = db.Column(db.Boolean, default=True)
    atendimentos = db.relationship('Atendimento', backref='paciente', lazy=True, cascade="all, delete")
    agendamentos = db.relationship('Agendamento', backref='paciente', lazy=True, cascade="all, delete")
    pagamentos = db.relationship('Pagamento', backref='paciente', lazy=True, cascade="all, delete")

class Pagamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('paciente.id'), nullable=False)
    descricao = db.Column(db.String(100), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pendente')  # 'pago' ou 'pendente'
    data = db.Column(db.Date, default=datetime.utcnow)


class Medico(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    especialidade = db.Column(db.String(100), nullable=False)
    crm = db.Column(db.String(20), nullable=False)
    telefone = db.Column(db.String(20))
    disponivel = db.Column(db.Boolean, default=True)
    agendamentos = db.relationship('Agendamento', backref='medico', lazy=True, cascade="all, delete")

class Agendamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('paciente.id'), nullable=False)
    medico_id = db.Column(db.Integer, db.ForeignKey('medico.id'), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    data = db.Column(db.Date, nullable=False)
    hora = db.Column(db.String(10), nullable=False)

class Atendimento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('paciente.id'), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    data = db.Column(db.DateTime, default=datetime.now)

from flask import request

@app.route('/')
def index():
    busca = request.args.get('busca')  

    if busca:
        pacientes = Paciente.query.filter(Paciente.nome.ilike(f'%{busca}%')).all()
    else:
        pacientes = Paciente.query.all()

    total_pacientes = db.session.query(func.count(Paciente.id)).scalar()
    idade_media = db.session.query(func.avg(Paciente.idade)).scalar()
    if idade_media:
        idade_media = round(idade_media, 1)

    paciente_mais_novo = db.session.query(Paciente).order_by(Paciente.idade.asc()).first()
    paciente_mais_velho = db.session.query(Paciente).order_by(Paciente.idade.desc()).first()

    return render_template(
        'index.html',
        pacientes=pacientes,
        total_pacientes=total_pacientes,
        idade_media=idade_media,
        paciente_mais_novo=paciente_mais_novo,
        paciente_mais_velho=paciente_mais_velho,
        busca=busca
    )


@app.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar():
    if request.method == 'POST':
        nome = request.form['nome']
        idade = request.form['idade']
        telefone = request.form['telefone']
        rg = request.form['rg']
        cpf = request.form['cpf']
        pagamentos_em_dia = True if request.form.get('pagamentos_em_dia') == 'on' else False

        novo_paciente = Paciente(
            nome=nome, 
            idade=idade, 
            telefone=telefone,
            rg=rg,
            cpf=cpf,
            pagamentos_em_dia=pagamentos_em_dia
        )
        db.session.add(novo_paciente)
        db.session.commit()
        return redirect(url_for('index'))

    return render_template('cadastrar.html')


@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    paciente = Paciente.query.get_or_404(id)
    if request.method == 'POST':
        paciente.nome = request.form['nome']
        paciente.idade = request.form['idade']
        paciente.telefone = request.form['telefone']
        paciente.rg = request.form['rg']
        paciente.cpf = request.form['cpf']
        paciente.pagamentos_em_dia = True if request.form.get('pagamentos_em_dia') == 'on' else False
        return redirect(url_for('index'))
    return render_template('editar.html', paciente=paciente)

@app.route('/excluir/<int:id>')
def excluir(id):
    paciente = Paciente.query.get_or_404(id)
    db.session.delete(paciente)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/cadastrar_medico', methods=['GET', 'POST'])
def cadastrar_medico():
    if request.method == 'POST':
        nome = request.form['nome']
        especialidade = request.form['especialidade']
        crm = request.form['crm']
        telefone = request.form['telefone']

        novo_medico = Medico(nome=nome, especialidade=especialidade, crm=crm, telefone=telefone)
        db.session.add(novo_medico)
        db.session.commit()
        return redirect(url_for('lista_medicos'))

    return render_template('cadastrar_medico.html')

@app.route('/medicos')
def lista_medicos():
    medicos = Medico.query.all()
    return render_template('medicos.html', medicos=medicos)

@app.route('/excluir_medico/<int:id>')
def excluir_medico(id):
    medico = Medico.query.get_or_404(id)
    db.session.delete(medico)
    db.session.commit()
    return redirect(url_for('lista_medicos'))

@app.route('/agendar', methods=['GET', 'POST'])
def agendar():
    pacientes = Paciente.query.all()
    medicos = Medico.query.all()

    if request.method == 'POST':
        paciente_id = request.form['paciente']
        medico_id = request.form['medico']
        tipo = request.form['tipo']
        data_str = request.form['data']
        hora = request.form['hora']

        data_obj = datetime.strptime(data_str, '%Y-%m-%d').date()

        novo_agendamento = Agendamento(
            paciente_id=paciente_id,
            medico_id=medico_id,
            tipo=tipo,
            data=data_obj,
            hora=hora
        )
        db.session.add(novo_agendamento)
        db.session.commit()
        return redirect(url_for('agendamentos'))

    return render_template('agendar.html', pacientes=pacientes, medicos=medicos)

@app.route('/agendamentos')
def agendamentos():
    agendamentos = Agendamento.query.order_by(Agendamento.data.desc()).all()
    return render_template('agendamentos.html', agendamentos=agendamentos)

from datetime import date

@app.route('/controle_acesso', methods=['GET', 'POST'])
def controle_acesso():
    pacientes = Paciente.query.all()
    medicos = Medico.query.filter_by(disponivel=True).all()  # só médicos disponíveis

    resultados = []

    for paciente in pacientes:
        pode_ser_atendido = True
        motivos = []

        # 1️⃣ Verificar se o paciente tem agendamento
        agendamento = Agendamento.query.filter_by(paciente_id=paciente.id).first()
        if not agendamento:
            pode_ser_atendido = False
            motivos.append("Sem agendamento marcado")

        # 2️⃣ Verificar documentos
        if not paciente.rg or not paciente.cpf:
            pode_ser_atendido = False
            motivos.append("Documentos incompletos")

        # 3️⃣ Verificar pagamento
        if not paciente.pagamentos_em_dia:
            pode_ser_atendido = False
            motivos.append("Pagamentos pendentes")

        # 4️⃣ Verificar médico disponível
        if not medicos:
            pode_ser_atendido = False
            motivos.append("Nenhum médico disponível")

        resultados.append({
            'paciente': paciente,
            'pode_ser_atendido': pode_ser_atendido,
            'motivos': motivos
        })

    return render_template('controle_acesso.html', resultados=resultados)



@app.route('/atendimentos', methods=['GET', 'POST'])
def atendimentos():
    pacientes = Paciente.query.all()

    if request.method == 'POST':
        paciente_id = request.form['paciente']
        tipo = request.form['tipo']
        descricao = request.form['descricao']

        novo_atendimento = Atendimento(
            paciente_id=paciente_id,
            tipo=tipo,
            descricao=descricao,
            data=datetime.now()
        )
        db.session.add(novo_atendimento)
        db.session.commit()
        return redirect(url_for('atendimentos'))

    atendimentos = Atendimento.query.order_by(Atendimento.data.desc()).all()
    return render_template('atendimentos.html', pacientes=pacientes, atendimentos=atendimentos)

if __name__ == '__main__':
    with app.app_context():
        # Deletar todas as tabelas antigas
        db.drop_all()
        # Criar tabelas novamente
        db.create_all()
    app.run(debug=True)
