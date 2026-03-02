from app import db
from app import login_manager
from flask_login import UserMixin
from datetime import datetime

class Usuario(UserMixin, db.Model):
    __tablename__ = "senha"
    __table_args__ = {"schema": "bdpbm"}

    idsenha = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String)
    status = db.Column(db.Boolean)
    usuario = db.Column(db.String)
    sexo = db.Column(db.String)
    email = db.Column(db.String)
    obm = db.Column(db.String)
    nivel = db.Column(db.Integer)
    senha = db.Column(db.String)   # 🔥 ESSA LINHA É ESSENCIAL
    data = db.Column(db.DateTime)
    dsc_programa = db.Column(db.String)
    funcao = db.Column(db.String)
    situacao = db.Column(db.Integer)
    telefone = db.Column(db.String)
    dataatualizacao = db.Column(db.DateTime)
    respalteracao = db.Column(db.BigInteger)

    def get_id(self):
        return str(self.idsenha)
    
@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))    



from datetime import datetime

class Ficha(db.Model):
    __tablename__ = "ficha"
    __table_args__ = {"schema": "bdpbm"}

    id = db.Column("idmatricula", db.Integer, primary_key=True)

    nome = db.Column(db.String(150))
    nomeguerra = db.Column(db.String(100))
    endereco = db.Column(db.String(200))
    turnopbm = db.Column(db.String(20))
    sexo = db.Column(db.String(20))
    datanascimento = db.Column(db.Date)
    cpf = db.Column(db.String(20))
    localpbm = db.Column(db.String(100))
    nomepai = db.Column(db.String(150))
    nomemae = db.Column(db.String(150))
    telpai = db.Column(db.String(20))
    telmae = db.Column(db.String(20))
    teloutros = db.Column(db.String(20))
    pessoaresp = db.Column(db.String(150))
    parentesco = db.Column(db.String(100))
    telresp = db.Column(db.String(20))
    email = db.Column(db.String(150))
    escola = db.Column(db.String(150))
    serie = db.Column(db.String(50))
    turnoescola = db.Column(db.String(20))
    situacao = db.Column(db.String(5))
    foto = db.Column(db.String(150))
    graduacao = db.Column(db.String(50))
    anoparticipou = db.Column(db.String(10))
    copiargresp = db.Column(db.String(5))
    certidaonasc = db.Column(db.String(5))
    publicarimagem = db.Column(db.String(1), nullable=False, default="N")
    autorizaausentar = db.Column(db.String(5))
    rotaonibus = db.Column(db.String(100))
    declaracaoescolar = db.Column(db.String(5))
    fotos = db.Column(db.String(150))
    respmatricula = db.Column(db.String(100))
    respalteracao = db.Column(db.String(100))
    dataregistro = db.Column(db.DateTime, default=datetime.utcnow)
    dataalteracao = db.Column(db.DateTime)
    altura = db.Column(db.String(10))
    peso = db.Column(db.String(10))
    renda = db.Column(db.String(20))
    pggoverno = db.Column(db.String(50))
    qualpgr = db.Column(db.String(100))
    pessoareside = db.Column(db.String(100))
    expbmparente = db.Column(db.String(5))
    anoex = db.Column(db.String(10))
    nomeex = db.Column(db.String(150))
    pessoastrabalham = db.Column(db.String(10))
    sangue = db.Column(db.String(5))
    possui_observacoes = db.Column(db.String(5))
    observacoes = db.Column(db.Text)
    dias_suspensao = db.Column(db.Integer)
    data_inicio_suspensao = db.Column(db.Date)
    desloca_sozinho = db.Column(db.String(5))
    possui_neurodivergencia = db.Column(db.String(5))
    numero_uniforme = db.Column(db.String(20))
    numero_calcado = db.Column(db.String(20))
    
class ChamadaDiaria(db.Model):
    __tablename__ = "chamada_diaria"
    __table_args__ = {"schema": "bdpbm"}

    id = db.Column(db.Integer, primary_key=True)
    idmatricula = db.Column(db.Integer, db.ForeignKey('bdpbm.ficha.idmatricula'))
    data_chamada = db.Column(db.Date)
    presenca = db.Column(db.Boolean)
    turno = db.Column(db.String(20))
    pelotao = db.Column(db.Integer)
    obm = db.Column(db.String(100))
    usuario_registro = db.Column(db.String(100))  
    
class Passeio(db.Model):
    __tablename__ = "passeios"
    __table_args__ = {"schema": "bdpbm"}

    id = db.Column("idpasseio", db.Integer, primary_key=True)
    nome_passeio = db.Column(db.String(200))
    data_passeio = db.Column(db.Date)
    hora_passeio = db.Column(db.Time)
    local_passeio = db.Column(db.String(200))
    obm = db.Column(db.String(100))
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)    