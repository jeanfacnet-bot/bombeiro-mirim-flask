from flask import Blueprint, render_template, session, redirect, url_for, request, flash, request, render_template, jsonify, send_file, current_app, abort
from app.models import Usuario, Ficha, ChamadaDiaria, Passeio
from app import db
from sqlalchemy import func, case, extract, text
from datetime import datetime, date
from flask_login import login_required, current_user, login_user, logout_user
import io
import os
from werkzeug.utils import secure_filename
import locale
from functools import wraps


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):

        if not current_user.is_authenticated:
            return redirect(url_for("main.login"))

        if current_user.nivel != 1:
            return redirect(url_for("main.dashboard"))  # igual seu PHP redirect

        return f(*args, **kwargs)

    return decorated_function

main = Blueprint("main", __name__)

@main.route("/login", methods=["GET", "POST"])
def login():

    error = None

    if request.method == "POST":

        usuario_digitado = request.form.get("usuario")
        senha_digitada = request.form.get("senha")

        usuario = Usuario.query.filter_by(
            usuario=usuario_digitado
        ).first()

        import hashlib
        senha_md5 = hashlib.md5(senha_digitada.encode()).hexdigest()

        if usuario and usuario.senha == senha_md5:
            login_user(usuario)
            return redirect(url_for("main.dashboard"))
        else:
            error = "Usuário ou senha inválidos"

    return render_template("login.html", error=error)


@main.route("/")
@login_required
def dashboard():
    
    # Redirecionamentos por nível
    if current_user.nivel == 7:
        return "Redirecionar para cadastro PBA"

    if current_user.nivel == 4:
        return "Redirecionar para externo"

    if current_user.nivel not in [1, 2, 3]:
        return redirect(url_for("main.login"))

    usuario = current_user
    
    from datetime import date

    hoje = date.today()

    # faixa etária 7–14 anos
    data_min_7_14 = date(hoje.year - 14, hoje.month, hoje.day)
    data_max_7_14 = date(hoje.year - 7, hoje.month, hoje.day)

    # exatamente 15 anos
    data_min_15 = date(hoje.year - 15, hoje.month, hoje.day)
    data_max_15 = date(hoje.year - 15, hoje.month, hoje.day)
    
    from sqlalchemy import text

    # Total ativos 7 a 14 anos
    if current_user.nivel in [2, 3]:

        total_ativos = db.session.execute(text("""
            SELECT COUNT(*) 
            FROM bdpbm.ficha
            WHERE situacao = '1'
            AND turnopbm <> 'RESERVA'
            AND UPPER(localpbm) = UPPER(:obm)
            AND datanascimento BETWEEN :data_min AND :data_max
        """), {
            "obm": usuario.obm,
            "data_min": data_min_7_14,
            "data_max": data_max_7_14
        }).scalar()

    else:

        total_ativos = db.session.execute(text("""
            SELECT COUNT(*) 
            FROM bdpbm.ficha
            WHERE situacao = '1'
            AND turnopbm <> 'RESERVA'
            AND datanascimento BETWEEN :data_min AND :data_max
        """)).scalar()
    
    # Total em RESERVA (7-14 anos da OBM do usuário)
    if current_user.nivel == 2:

        total_reserva = db.session.execute(text("""
            SELECT COUNT(*) 
            FROM bdpbm.ficha
            WHERE situacao = '1'
            AND turnopbm = 'RESERVA'
            AND UPPER(localpbm) = UPPER(:obm)
            AND datanascimento BETWEEN :data_min AND :data_max
        """), {
            "obm": usuario.obm,
            "data_min": data_min_7_14,
            "data_max": data_max_7_14
        }).scalar()

    else:

        total_reserva = db.session.execute(text("""
            SELECT COUNT(*) 
            FROM bdpbm.ficha
            WHERE situacao = '1'
            AND turnopbm = 'RESERVA'
            AND datanascimento BETWEEN :data_min AND :data_max
        """)).scalar()


    # Jovem Candango (14-15 anos ativos)
    total_jovem_candango = db.session.execute(text("""
        SELECT COUNT(*) 
        FROM bdpbm.ficha
        WHERE situacao = '1'
        AND turnopbm <> 'RESERVA'
        AND date_part('year', age(current_date, datanascimento)) BETWEEN 14 AND 15
    """)).scalar()


    # Total de registros
    if current_user.nivel == 2:

        total_registros = db.session.execute(text("""
            SELECT COUNT(*)
            FROM bdpbm.ficha
            WHERE situacao = '1'
            AND UPPER(localpbm) = UPPER(:obm)
        """), {
            "obm": usuario.obm,
            "data_min": data_min_7_14,
            "data_max": data_max_7_14
        }).scalar()

    else:

        total_registros = db.session.execute(text("""
            SELECT COUNT(*)
            FROM bdpbm.ficha
            WHERE situacao = '1'
        """)).scalar()
    
    # Total MATUTINO (7-14 anos da OBM do usuário)
    total_matutino = db.session.execute(text("""
        SELECT COUNT(*) 
        FROM bdpbm.ficha
        WHERE situacao = '1'
        AND turnopbm = 'MATUTINO'
        AND UPPER(localpbm) = UPPER(:obm)
        AND datanascimento BETWEEN :data_min AND :data_max
    """), {
            "obm": usuario.obm,
            "data_min": data_min_7_14,
            "data_max": data_max_7_14
        }).scalar()


    # Total VESPERTINO (7-14 anos da OBM do usuário)
    total_vespertino = db.session.execute(text("""
        SELECT COUNT(*) 
        FROM bdpbm.ficha
        WHERE situacao = '1'
        AND turnopbm = 'VESPERTINO'
        AND UPPER(localpbm) = UPPER(:obm)
        AND datanascimento BETWEEN :data_min AND :data_max
    """), {
            "obm": usuario.obm,
            "data_min": data_min_7_14,
            "data_max": data_max_7_14
        }).scalar()


    # Total Neurodivergentes
    if current_user.nivel == 2:

        total_neuro = db.session.execute(text("""
            SELECT COUNT(*) 
            FROM bdpbm.ficha
            WHERE situacao = '1'
            AND possui_neurodivergencia = 'sim'
            AND UPPER(localpbm) = UPPER(:obm)
        """), {
            "obm": usuario.obm,
            "data_min": data_min_7_14,
            "data_max": data_max_7_14
        }).scalar()

    else:

        total_neuro = db.session.execute(text("""
            SELECT COUNT(*) 
            FROM bdpbm.ficha
            WHERE situacao = '1'
            AND possui_neurodivergencia = 'sim'
        """)).scalar()
    
    # Totais por Localidade (7-14 e 15 anos)
    totais_localidade = db.session.execute(text("""
        SELECT 
            localpbm,
            COUNT(*) FILTER (
                WHERE datanascimento BETWEEN :data_min AND :data_max
            ) as total_7_14,
            COUNT(*) FILTER (
                WHERE date_part('year', age(current_date, datanascimento)) = 15
            ) as total_15
        FROM bdpbm.ficha
        WHERE situacao = '1'
        AND turnopbm <> 'RESERVA'
        GROUP BY localpbm
        ORDER BY localpbm ASC
    """), {
        "data_min": data_min_7_14,
        "data_max": data_max_7_14
    }).fetchall()
    
    # -------- ROTAS (apenas se OBM for Ceilândia) --------
    rotas = []

    if usuario.obm.strip().upper() == "CEILÂNDIA":
        rotas = db.session.execute(text("""
            SELECT rotaonibus, turnopbm, COUNT(*) as total
            FROM bdpbm.ficha
            WHERE situacao = '1'
            AND turnopbm <> 'RESERVA'
            AND rotaonibus IS NOT NULL
            AND rotaonibus <> ''
            AND UPPER(localpbm) = UPPER(:obm)
            GROUP BY rotaonibus, turnopbm
            ORDER BY rotaonibus, turnopbm
        """), {"obm": usuario.obm}).fetchall()

    return render_template(
        "index.html",
        usuario=usuario,
        total_ativos=total_ativos,
        total_reserva=total_reserva,
        total_jovem_candango=total_jovem_candango,
        total_registros=total_registros,
        total_matutino=total_matutino,
        total_vespertino=total_vespertino,
        total_neuro=total_neuro,
        totais_localidade=totais_localidade,
        rotas=rotas,
        externo=False
    )
    
@main.route("/cadastrar", methods=["POST"])
def cadastrar():

    externo = request.form.get("origem") == "externo"
    usuario = current_user if current_user.is_authenticated else None

    def get(nome):
        return request.form.get(nome)

    def get_int_bool(nome):
        valor = request.form.get(nome)
        return int(valor) if valor in ["0", "1"] else 0

    datanascimento = get("datanascimento")
    if datanascimento:
        datanascimento = datetime.strptime(datanascimento, "%Y-%m-%d").date()

        idade = date.today().year - datanascimento.year - (
            (date.today().month, date.today().day) <
            (datanascimento.month, datanascimento.day)
        )

        if idade < 7 or idade > 15:
            flash("Idade permitida é entre 7 e 15 anos.", "danger")
            if externo:
                return redirect(url_for("main.inscricao"))
            else:
                return redirect(url_for("main.dashboard"))

    nova_ficha = Ficha(
        nome=get("nome"),
        nomeguerra=get("nomeguerra") or None,
        sexo=get("sexo"),
        cpf=get("cpf"),
        datanascimento=datanascimento,
        sangue=get("sangue"),
        situacao="1",
        turnopbm=get("turnopbm"),
        localpbm=usuario.obm if usuario else request.form.get("localpbm"),
        endereco=get("endereco"),
        teloutros=get("tel"),
        email=get("email"),
        nomepai=get("nomepai"),
        telpai=get("telpai"),
        nomemae=get("nomemae"),
        telmae=get("telmae"),
        pessoaresp=get("pessoaresp"),
        parentesco=get("parentesco"),
        telresp=get("telresp"),
        escola=get("escola"),
        serie=get("serie"),
        turnoescola=get("turnoescola"),
        altura=get("altura") or None,
        peso=get("peso") or None,
        pggoverno=get_int_bool("pggoverno"),
        rotaonibus=get("rotaonibus"),
        expbmparente=get_int_bool("expbmparente"),
        nomeex=get("nomeex"),
        possui_observacoes=get_int_bool("possui_observacoes"),
        possui_neurodivergencia=get_int_bool("possui_neurodivergencia"),
        desloca_sozinho=get_int_bool("desloca_sozinho"),
        observacoes=get("observacoes"),
        dataregistro=datetime.now(),

        # 👇 IMPORTANTE
        publicarimagem=0,
        autorizaausentar=0,
        copiargresp=0,
        certidaonasc=0,
        declaracaoescolar=0,
        fotos=0
    )
    
    # 🔥 VALIDAÇÃO OBRIGATÓRIA

    campos_obrigatorios = [
        "nome",
        "sexo",
        "datanascimento",
        "cpf",
        "pessoaresp",
        "telresp",
        "escola",
        "serie",
        "turnoescola"
    ]

    for campo in campos_obrigatorios:
        print(campo, "=", request.form.get(campo))
        
    for campo in campos_obrigatorios:
        valor = request.form.get(campo)

        if valor is None or valor.strip() == "":
            flash(f"O campo {campo} é obrigatório.", "danger")
            if externo:
                return redirect(url_for("main.inscricao"))
            else:
                return redirect(url_for("main.dashboard"))
    
    cpf = request.form.get("cpf")

    cpf_existente = Ficha.query.filter_by(cpf=cpf).first()

    if cpf_existente:
        flash("CPF já cadastrado no sistema.", "danger")
        if externo:
            return redirect(url_for("main.inscricao"))
        else:
            return redirect(url_for("main.dashboard"))

    for campo in campos_obrigatorios:
        if not request.form.get(campo):
            flash("Preencha todos os campos obrigatórios.", "danger")
            if externo:
                return redirect(url_for("main.inscricao"))
            else:
                return redirect(url_for("main.dashboard"))

    db.session.add(nova_ficha)
    db.session.commit()
    
    flash("Aluno cadastrado com sucesso!", "success")

    if externo:
        return redirect(url_for("main.inscricao"))
    else:
        return redirect(url_for("main.dashboard"))
    
@main.route("/verificar_nome")
def verificar_nome():
    nome = request.args.get("nome")

    ficha = Ficha.query.filter_by(nome=nome).first()

    if ficha:
        return {"existe": True, "id": ficha.id}
    else:
        return {"existe": False}



@main.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):

    ficha = Ficha.query.get_or_404(id)
    
    # ===== BUSCAR HISTÓRICOS SEMPRE =====
    historicos = db.session.execute(text("""
        SELECT *
        FROM bdpbm.historico
        WHERE idmatricula = :id
        ORDER BY data DESC
    """), {"id": id}).fetchall()

    # -------- FUNÇÃO DE CÁLCULO AUTOMÁTICO ----------
    def calcular_dias_restantes(dias_total, data_inicio):
        if not dias_total or not data_inicio:
            return 0

        dias_passados = (date.today() - data_inicio).days
        restante = dias_total - dias_passados

        return restante if restante > 0 else 0

    # -------- ATUALIZA AUTOMATICAMENTE SE NECESSÁRIO ----------
    dias_restantes = calcular_dias_restantes(
        ficha.dias_suspensao,
        ficha.data_inicio_suspensao
    )

    if dias_restantes != ficha.dias_suspensao:
        if dias_restantes > 0:
            ficha.dias_suspensao = dias_restantes
        else:
            ficha.dias_suspensao = 0
            ficha.data_inicio_suspensao = None

        db.session.commit()

    # -------- CALCULAR IDADE ----------
    idade = None
    if ficha.datanascimento:
        hoje = date.today()
        idade = hoje.year - ficha.datanascimento.year - (
            (hoje.month, hoje.day) < (ficha.datanascimento.month, ficha.datanascimento.day)
        )

    # -------- SE FOR POST (SALVAR ALTERAÇÃO) ----------
    if request.method == "POST":

        ficha.nome = request.form.get("nome")
        nomeguerra = request.form.get("nomeguerra")

        if nomeguerra and nomeguerra.strip() != "":
            ficha.nomeguerra = nomeguerra.strip()
        else:
            ficha.nomeguerra = None
        ficha.endereco = request.form.get("endereco")
        ficha.turnopbm = request.form.get("turnopbm")
        ficha.sexo = request.form.get("sexo")
        ficha.cpf = request.form.get("cpf")
        ficha.localpbm = request.form.get("localpbm")
        ficha.nomepai = request.form.get("nomepai")
        ficha.nomemae = request.form.get("nomemae")
        ficha.telpai = request.form.get("telpai")
        ficha.telmae = request.form.get("telmae")
        ficha.pessoaresp = request.form.get("pessoaresp")
        ficha.parentesco = request.form.get("parentesco")
        ficha.telresp = request.form.get("telresp")
        ficha.email = request.form.get("email")
        ficha.escola = request.form.get("escola")
        ficha.serie = request.form.get("serie")
        ficha.turnoescola = request.form.get("turnoescola")
        ficha.situacao = request.form.get("situacao")
        ficha.graduacao = request.form.get("graduacao")
        ficha.rotaonibus = request.form.get("rotaonibus")
        ficha.numero_uniforme = request.form.get("numero_uniforme")
        ficha.numero_calcado = request.form.get("numero_calcado")
        ficha.sangue = request.form.get("sangue")
        ficha.possui_observacoes = request.form.get("possui_observacoes")
        ficha.observacoes = request.form.get("observacoes")
        ficha.possui_neurodivergencia = request.form.get("possui_neurodivergencia")
        ficha.desloca_sozinho = request.form.get("desloca_sozinho")

        # -------- LÓGICA DA SUSPENSÃO ----------
        dias_antigos = ficha.dias_suspensao
        dias_novos = int(request.form.get("dias_suspensao") or 0)

        if dias_novos == 0:
            ficha.data_inicio_suspensao = None
        else:
            if dias_novos != dias_antigos:
                ficha.data_inicio_suspensao = date.today()

        ficha.dias_suspensao = dias_novos

        db.session.commit()

        flash("Aluno atualizado com sucesso!", "success")
        return redirect(url_for("main.editar", id=id))
        
        
    # -------- RENDERIZA TELA ----------
    return render_template(
        "editar.html",
        ficha=ficha,
        idade=idade,
        historicos=historicos
    )

@main.route("/buscar_alunos")
@login_required
def buscar_alunos():

    termo = request.args.get("q", "").strip()

    if len(termo) < 2:
        return jsonify([])

    alunos = Ficha.query.filter(
        Ficha.nome.ilike(f"%{termo}%"),
        func.upper(Ficha.localpbm) == current_user.obm.upper()
    ).order_by(Ficha.nome).limit(10).all()

    resultado = [
        {"id": aluno.id, "nome": aluno.nome}
        for aluno in alunos
    ]

    return jsonify(resultado)   
    
@main.route("/reserva")
def reserva():

    if not current_user.is_authenticated:
        return redirect(url_for("main.login"))

    usuario = current_user

    hoje = date.today()

    alunos = Ficha.query.filter(
        Ficha.situacao == "1",
        Ficha.turnopbm == "RESERVA",
        func.upper(Ficha.localpbm) == usuario.obm.upper()
    ).order_by(Ficha.dataregistro.desc()).all()

    lista_matutino = []
    lista_vespertino = []

    for aluno in alunos:

        if not aluno.datanascimento:
            continue

        idade = hoje.year - aluno.datanascimento.year - (
            (hoje.month, hoje.day) < (aluno.datanascimento.month, aluno.datanascimento.day)
        )

        if 7 <= idade <= 14:

            if aluno.turnoescola and aluno.turnoescola.lower() == "matutino":
                lista_matutino.append((aluno, idade))

            elif aluno.turnoescola and aluno.turnoescola.lower() == "vespertino":
                lista_vespertino.append((aluno, idade))

    return render_template(
        "reserva.html",
        usuario=usuario,
        lista_matutino=lista_matutino,
        lista_vespertino=lista_vespertino
    )    
    
from datetime import date

@main.route("/chamada")
def chamada():

    if not current_user.is_authenticated:
        return redirect(url_for("main.login"))

    usuario = current_user
    hoje = date.today()

    alunos = Ficha.query.filter(
        func.upper(Ficha.localpbm) == usuario.obm.upper(),
        Ficha.situacao == "1",
        Ficha.turnopbm != "RESERVA"
    ).order_by(Ficha.nome.asc()).all()

    estrutura = {
        "Matutino": [],
        "Vespertino": []
    }

    pelotoes = [
        {"nome": "3º PELOTÃO", "min": 12, "max": 14},
        {"nome": "2º PELOTÃO", "min": 10, "max": 11},
        {"nome": "1º PELOTÃO", "min": 7, "max": 9}
    ]

    for turno in ["Matutino", "Vespertino"]:

        alunos_turno = []

        for aluno in alunos:

            if aluno.turnopbm.lower() != turno.lower():
                continue

            if not aluno.datanascimento:
                continue

            idade = hoje.year - aluno.datanascimento.year - (
                (hoje.month, hoje.day) <
                (aluno.datanascimento.month, aluno.datanascimento.day)
            )

            for pelotao in pelotoes:
                if pelotao["min"] <= idade <= pelotao["max"]:

                    # Suspensão
                    dias_restantes = ""
                    if aluno.dias_suspensao and aluno.data_inicio_suspensao:
                        dias_passados = (hoje - aluno.data_inicio_suspensao).days
                        restante = aluno.dias_suspensao - dias_passados
                        if restante > 0:
                            dias_restantes = restante

                    alunos_turno.append({
                        "pelotao": pelotao["nome"],
                        "aluno": aluno,
                        "idade": idade,
                        "suspenso": dias_restantes != ""
                    })

        estrutura[turno] = alunos_turno
        
    # ==============================
    # LISTA POR ROTA (SOMENTE CEILÂNDIA)
    # ==============================

    # ==============================
    # LISTA POR ROTA SEPARADA POR TURNO (IGUAL PHP)
    # ==============================

    rotas_estrutura = {
        "MATUTINO": {},
        "VESPERTINO": {}
    }

    if usuario.obm.upper() == "CEILÂNDIA":

        for turno in ["MATUTINO", "VESPERTINO"]:

            rotas = db.session.query(
                Ficha.rotaonibus
            ).filter(
                Ficha.situacao == "1",
                func.upper(Ficha.localpbm) == usuario.obm.upper(),
                func.upper(Ficha.turnopbm) == turno,
                Ficha.rotaonibus != None,
                Ficha.rotaonibus != ""
            ).distinct().order_by(Ficha.rotaonibus).all()

            for rota_tuple in rotas:

                rota = rota_tuple[0]

                alunos_rota = Ficha.query.filter(
                    Ficha.situacao == "1",
                    func.upper(Ficha.localpbm) == usuario.obm.upper(),
                    func.upper(Ficha.turnopbm) == turno,
                    Ficha.rotaonibus == rota
                ).order_by(Ficha.nome).all()

                lista_alunos = []

                for aluno in alunos_rota:

                    if not aluno.datanascimento:
                        continue

                    idade = hoje.year - aluno.datanascimento.year - (
                        (hoje.month, hoje.day) <
                        (aluno.datanascimento.month, aluno.datanascimento.day)
                    )

                    lista_alunos.append({
                        "aluno": aluno,
                        "idade": idade
                    })

                rotas_estrutura[turno][rota] = lista_alunos  

    return render_template(
        "chamada.html",
        usuario=usuario,
        estrutura=estrutura,
        rotas_estrutura=rotas_estrutura
    )    
    
@main.route("/chamada_diaria", methods=["GET", "POST"])
def chamada_diaria():

    if not current_user.is_authenticated:
        return redirect(url_for("main.login"))

    usuario = current_user
    hoje = date.today()

    if request.method == "POST":

        turno = request.form.get("turno")
        pelotao = int(request.form.get("pelotao"))

        # 🔥 PADRONIZA OBM
        obm_usuario = usuario.obm.upper().strip()

        # ===== VERIFICA DUPLICIDADE =====
        existe = ChamadaDiaria.query.filter(
            ChamadaDiaria.data_chamada == hoje,
            ChamadaDiaria.turno == turno,
            ChamadaDiaria.pelotao == pelotao,
            func.upper(ChamadaDiaria.obm) == obm_usuario
        ).first()

        if existe:
            flash("Já existe chamada registrada para hoje!", "danger")
            return redirect(url_for("main.chamada_diaria"))

        # ===== PERCORRE TODOS OS INPUTS status_ =====
        registros_criados = 0

        for key in request.form:

            if key.startswith("status_"):

                aluno_id = key.replace("status_", "")
                status = request.form.get(key) == "1"

                aluno = Ficha.query.get(int(aluno_id))

                if not aluno:
                    continue

                nova = ChamadaDiaria(
                    idmatricula=aluno.id,
                    data_chamada=hoje,
                    presenca=status,
                    turno=turno,
                    pelotao=pelotao,
                    obm=obm_usuario,
                    usuario_registro=usuario.usuario
                )

                db.session.add(nova)
                registros_criados += 1

        if registros_criados == 0:
            flash("Nenhum aluno foi enviado no formulário.", "danger")
            return redirect(url_for("main.chamada_diaria"))

        db.session.commit()

        flash("Chamada registrada com sucesso!", "success")
        return redirect(url_for("main.chamada_diaria"))

    return render_template("chamada_diaria.html", usuario=usuario)    
    
    
@main.route("/buscar_alunos_chamada", methods=["POST"])
def buscar_alunos_chamada():

    turno = request.form.get("turno")
    pelotao = int(request.form.get("pelotao"))

    hoje = date.today()

    pelotoes = {
        1: (7,9),
        2: (10,11),
        3: (12,14)
    }

    idade_min, idade_max = pelotoes[pelotao]

    alunos = Ficha.query.filter(
        Ficha.turnopbm == turno,
        Ficha.situacao == "1",
        Ficha.turnopbm != "RESERVA"
    ).order_by(Ficha.nome.asc()).all()

    resultado = []

    for aluno in alunos:
        if not aluno.datanascimento:
            continue

        idade = hoje.year - aluno.datanascimento.year - (
            (hoje.month, hoje.day) <
            (aluno.datanascimento.month, aluno.datanascimento.day)
        )

        if idade_min <= idade <= idade_max:
            resultado.append(aluno)

    return render_template("partials/_lista_chamada.html", alunos=resultado)  
    
@main.route("/logout")
def logout():
    logout_user()
    flash("Você saiu do sistema.", "success")
    return redirect(url_for("main.login"))    
    
@main.route("/relatorio-chamada")
@login_required
def relatorio_chamada():

    data_busca = request.args.get("data")
    turno_busca = request.args.get("turno")
    pelotao_busca = request.args.get("pelotao")
    nome_busca = request.args.get("nome")
    presenca_busca = request.args.get("presenca")

    query = db.session.query(
        ChamadaDiaria,
        Ficha.nome
    ).join(Ficha, ChamadaDiaria.idmatricula == Ficha.id)

    query = query.filter(
        func.upper(ChamadaDiaria.obm) == current_user.obm.upper()
    )

    if data_busca:
        data_convertida = datetime.strptime(data_busca, "%Y-%m-%d").date()
        query = query.filter(ChamadaDiaria.data_chamada == data_convertida)

    if turno_busca:
        query = query.filter(ChamadaDiaria.turno == turno_busca)

    if pelotao_busca:
        query = query.filter(ChamadaDiaria.pelotao == int(pelotao_busca))

    if nome_busca:
        query = query.filter(Ficha.nome.ilike(f"%{nome_busca}%"))

    if presenca_busca != "" and presenca_busca is not None:
        if presenca_busca == "1":
            query = query.filter(ChamadaDiaria.presenca == True)
        else:
            query = query.filter(ChamadaDiaria.presenca == False)

    chamadas = query.order_by(
        ChamadaDiaria.data_chamada.desc(),
        ChamadaDiaria.turno,
        ChamadaDiaria.pelotao,
        Ficha.nome
    ).limit(1000).all()

    # ===== ALUNOS MAIS FALTOSOS =====
    faltosos_query = db.session.query(
        Ficha.nome.label("nome"),
        Ficha.telpai.label("telpai"),
        Ficha.telmae.label("telmae"),
        Ficha.telresp.label("telresp"),
        func.sum(
            case((ChamadaDiaria.presenca == False, 1), else_=0)
        ).label("total_faltas")
    ).join(
        ChamadaDiaria, Ficha.id == ChamadaDiaria.idmatricula
    ).filter(
        func.upper(Ficha.localpbm) == current_user.obm.upper(),
        Ficha.situacao == "1",
        Ficha.turnopbm != "RESERVA"
    ).group_by(
        Ficha.id,
        Ficha.nome,
        Ficha.telpai,
        Ficha.telmae,
        Ficha.telresp
    ).order_by(
        func.sum(
            case((ChamadaDiaria.presenca == False, 1), else_=0)
        ).desc()
    ).limit(10)

    faltosos = [dict(r._mapping) for r in faltosos_query.all()]

    # ===== RESUMO =====
    resumo_query = db.session.query(
        ChamadaDiaria.turno.label("turno"),
        ChamadaDiaria.pelotao.label("pelotao"),
        func.count(func.distinct(ChamadaDiaria.idmatricula)).label("total_alunos"),
        func.sum(
            case((ChamadaDiaria.presenca == True, 1), else_=0)
        ).label("total_presentes"),
        func.sum(
            case((ChamadaDiaria.presenca == False, 1), else_=0)
        ).label("total_faltas"),
        func.round(
            (
                func.sum(
                    case((ChamadaDiaria.presenca == True, 1), else_=0)
                ) * 100.0
            ) / func.count(ChamadaDiaria.id),
            1
        ).label("percentual_presenca")
    ).filter(
        func.upper(ChamadaDiaria.obm) == current_user.obm.upper()
    ).group_by(
        ChamadaDiaria.turno,
        ChamadaDiaria.pelotao,
        ChamadaDiaria.data_chamada
    ).order_by(
        ChamadaDiaria.turno,
        ChamadaDiaria.pelotao,
        ChamadaDiaria.data_chamada
    )

    resumo = [dict(r._mapping) for r in resumo_query.all()]

    return render_template(
        "relatorio_chamada.html",
        chamadas=chamadas,
        faltosos=faltosos,
        resumo=resumo
    )
    
@main.route("/toggle-presenca", methods=["POST"])
@login_required
def toggle_presenca():

    id = request.form.get("id")
    nova_presenca = request.form.get("presenca")

    chamada = ChamadaDiaria.query.get(id)

    if not chamada:
        return jsonify(success=False)

    chamada.presenca = int(nova_presenca)
    db.session.commit()

    return jsonify(success=True)    
    
@main.route("/aniversariantes")
@login_required
def aniversariantes():

    usuario = current_user

    # Mês selecionado (igual PHP)
    selected_month = request.args.get("month", default=date.today().month, type=int)

    # Query igual ao PHP
    aniversariantes = db.session.query(
        Ficha.nome,
        Ficha.datanascimento,
        Ficha.turnopbm
    ).filter(
        extract("month", Ficha.datanascimento) == selected_month,
        Ficha.situacao == "1",
        func.upper(Ficha.localpbm) == usuario.obm.upper(),
        Ficha.turnopbm != "RESERVA"
    ).order_by(
        Ficha.turnopbm,
        extract("day", Ficha.datanascimento),
        Ficha.nome
    ).all()

    hoje = date.today()

    morning_birthdays = []
    afternoon_birthdays = []

    for aluno in aniversariantes:

        idade = hoje.year - aluno.datanascimento.year

        item = {
            "nome": aluno.nome.upper(),
            "data": aluno.datanascimento.strftime("%d/%m/%Y").upper(),
            "idade": idade
        }

        if aluno.turnopbm.upper() == "MATUTINO":
            morning_birthdays.append(item)
        else:
            afternoon_birthdays.append(item)

    months = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março",
        4: "Abril", 5: "Maio", 6: "Junho",
        7: "Julho", 8: "Agosto", 9: "Setembro",
        10: "Outubro", 11: "Novembro", 12: "Dezembro"
    }

    return render_template(
        "aniversariantes.html",
        selected_month=selected_month,
        months=months,
        morning_birthdays=morning_birthdays,
        afternoon_birthdays=afternoon_birthdays,
        usuario=usuario
    )

@main.route("/ex-bbmirins")
@login_required
def ex_bbmirins():

    usuario = current_user
    filtronome = request.args.get("filtronome", "")

    hoje = date.today()

    alunos = Ficha.query.filter(
        func.upper(Ficha.localpbm) == usuario.obm.upper(),
        Ficha.nome.ilike(f"%{filtronome}%")
    ).order_by(Ficha.nome).all()

    ex_alunos = []

    for aluno in alunos:

        if not aluno.datanascimento:
            continue

        # Cálculo idêntico ao PHP:
        idade = hoje.year - aluno.datanascimento.year - (
            (hoje.month, hoje.day) <
            (aluno.datanascimento.month, aluno.datanascimento.day)
        )

        if idade >= 15:
            ex_alunos.append({
                "id": aluno.id,
                "nome": aluno.nome,
                "foto": aluno.foto,
                "idade": idade
            })

    total = len(ex_alunos)

    return render_template(
        "ex_bbmirins.html",
        ex_alunos=ex_alunos,
        total=total,
        filtronome=filtronome
    )

@main.route("/ajuda")
@login_required
def ajuda():
    return render_template("ajuda.html")


@main.route("/lista-pais")
@login_required
def lista_pais():

    usuario = current_user
    hoje = date.today()

    alunos = Ficha.query.filter(
        func.upper(Ficha.localpbm) == usuario.obm.upper(),
        Ficha.situacao == "1",
        Ficha.turnopbm != "0",
        Ficha.turnopbm != "RESERVA"
    ).order_by(
        Ficha.turnopbm,
        Ficha.nome
    ).all()

    alunos_por_turno = {}

    for aluno in alunos:

        if not aluno.datanascimento:
            continue

        idade = hoje.year - aluno.datanascimento.year - (
            (hoje.month, hoje.day) <
            (aluno.datanascimento.month, aluno.datanascimento.day)
        )

        if 7 <= idade <= 14:
            turno = aluno.turnopbm

            if turno not in alunos_por_turno:
                alunos_por_turno[turno] = []

            alunos_por_turno[turno].append(aluno)

    return render_template(
        "lista_pais.html",
        alunos_por_turno=alunos_por_turno,
        usuario=usuario
    )

@main.route("/uniforme-calcado", methods=["GET", "POST"])
@login_required
def uniforme_calcado():

    usuario = current_user
    obm = usuario.obm
    hoje = date.today()

    # ===== SALVAR ALTERAÇÃO =====
    if request.method == "POST":

        ids = request.form.getlist("idmatricula[]")

        for id in ids:
            numero_uniforme = request.form.get(f"numero_uniforme[{id}]")
            numero_calcado = request.form.get(f"numero_calcado[{id}]")

            aluno = Ficha.query.get(int(id))

            if aluno:
                aluno.numero_uniforme = numero_uniforme
                aluno.numero_calcado = numero_calcado

        db.session.commit()
        return redirect(url_for("main.uniforme_calcado"))

    # ===== TOTAL POR UNIFORME =====
    uniformes = db.session.query(
        Ficha.numero_uniforme,
        func.count(Ficha.id)
    ).filter(
        Ficha.situacao == "1",
        func.upper(Ficha.localpbm) == obm.upper(),
        func.upper(Ficha.turnopbm).in_(["MATUTINO", "VESPERTINO"]),
        Ficha.numero_uniforme != ""
    ).group_by(
        Ficha.numero_uniforme
    ).order_by(
        Ficha.numero_uniforme
    ).all()

    # ===== TOTAL POR CALÇADO =====
    calcados = db.session.query(
        Ficha.numero_calcado,
        func.count(Ficha.id)
    ).filter(
        Ficha.situacao == "1",
        func.upper(Ficha.localpbm) == obm.upper(),
        func.upper(Ficha.turnopbm).in_(["MATUTINO", "VESPERTINO"]),
        Ficha.numero_calcado != ""
    ).group_by(
        Ficha.numero_calcado
    ).order_by(
        Ficha.numero_calcado
    ).all()

    from collections import defaultdict

    # ===== LISTA AGRUPADA POR TURNO E PELOTÃO =====
    alunos = Ficha.query.filter(
        Ficha.situacao == "1",
        func.upper(Ficha.localpbm) == obm.upper(),
        func.upper(Ficha.turnopbm).in_(["MATUTINO", "VESPERTINO"])
    ).order_by(
        Ficha.turnopbm,
        Ficha.nome
    ).all()

    estrutura = defaultdict(lambda: defaultdict(list))

    for aluno in alunos:

        if not aluno.datanascimento:
            continue

        idade = hoje.year - aluno.datanascimento.year - (
            (hoje.month, hoje.day) <
            (aluno.datanascimento.month, aluno.datanascimento.day)
        )

        if 7 <= idade <= 9:
            pelotao = "1"
        elif 10 <= idade <= 11:
            pelotao = "2"
        elif 12 <= idade <= 14:
            pelotao = "3"
        else:
            continue

        estrutura[aluno.turnopbm][pelotao].append(aluno)

    # 🔥 RETURN FORA DO LOOP
    return render_template(
        "uniforme_calcado.html",
        uniformes=uniformes,
        calcados=calcados,
        estrutura=estrutura,
        obm=obm
    )

@main.route("/passeios", methods=["GET", "POST"])
@login_required
def passeios():

    usuario = current_user
    obm = usuario.obm

    # ==========================
    # CRIAR PASSEIO
    # ==========================
    if request.method == "POST" and "criar_passeio" in request.form:

        nome = request.form.get("nome_passeio")
        data = request.form.get("data_passeio")
        hora = request.form.get("hora_passeio")
        local = request.form.get("local_passeio")

        novo = Passeio(
            nome_passeio=nome,
            data_passeio=datetime.strptime(data, "%Y-%m-%d").date(),
            hora_passeio=datetime.strptime(hora, "%H:%M").time(),
            local_passeio=local,
            obm=obm
        )

        db.session.add(novo)
        db.session.commit()

        return redirect(url_for("main.passeios"))

    # ==========================
    # EXCLUIR PASSEIO
    # ==========================
    excluir_id = request.args.get("excluir")

    if excluir_id:
        passeio = Passeio.query.filter_by(id=int(excluir_id), obm=obm).first()
        if passeio:
            db.session.delete(passeio)
            db.session.commit()
        return redirect(url_for("main.passeios"))

    # ==========================
    # LISTAR PASSEIOS
    # ==========================
    lista = Passeio.query.filter_by(
        obm=obm
    ).order_by(
        Passeio.data_criacao.desc()
    ).all()

    return render_template(
        "passeios.html",
        lista=lista,
        obm=obm
    )
    
@main.route("/gerenciar-passeio/<int:id>", methods=["GET", "POST"])
@login_required
def gerenciar_passeio(id):

    usuario = current_user
    hoje = date.today()

    passeio = Passeio.query.get_or_404(id)

    # ==============================
    # ADICIONAR ALUNOS
    # ==============================
    if request.method == "POST" and "adicionar" in request.form:

        alunos_ids = request.form.getlist("alunos[]")

        for aluno_id in alunos_ids:

            existe = db.session.execute(text("""
                SELECT 1 FROM bdpbm.passeio_alunos
                WHERE idpasseio = :idpasseio
                AND idmatricula = :idmatricula
            """), {
                "idpasseio": id,
                "idmatricula": aluno_id
            }).fetchone()

            if not existe:
                db.session.execute(text("""
                    INSERT INTO bdpbm.passeio_alunos (idpasseio, idmatricula)
                    VALUES (:idpasseio, :idmatricula)
                """), {
                    "idpasseio": id,
                    "idmatricula": aluno_id
                })

        db.session.commit()
        return redirect(url_for("main.gerenciar_passeio", id=id))
        
    # ==============================
    # REMOVER VÁRIOS
    # ==============================
    if request.method == "POST" and request.form.get("acao") == "remover_varios":

        remover_ids = request.form.getlist("remover_ids[]")

        for aluno_id in remover_ids:
            db.session.execute(text("""
                DELETE FROM bdpbm.passeio_alunos
                WHERE idpasseio = :id
                AND idmatricula = :idmatricula
            """), {
                "id": id,
                "idmatricula": aluno_id
            })

        db.session.commit()
        return redirect(url_for("main.gerenciar_passeio", id=id))   

    # ==============================
    # REMOVER ALUNO
    # ==============================
    remover = request.args.get("remover")

    if remover:
        db.session.execute(text("""
            DELETE FROM bdpbm.passeio_alunos
            WHERE idpasseio = :id
            AND idmatricula = :idmatricula
        """), {
            "id": id,
            "idmatricula": remover
        })
        db.session.commit()
        return redirect(url_for("main.gerenciar_passeio", id=id))

    # ==============================
    # ALUNOS DO PASSEIO
    # ==============================
    alunos_passeio = db.session.execute(text("""
        SELECT f.*
        FROM bdpbm.passeio_alunos pa
        JOIN bdpbm.ficha f ON f.idmatricula = pa.idmatricula
        WHERE pa.idpasseio = :id
        ORDER BY f.nome
    """), {"id": id}).fetchall()

    # ==============================
    # IDS JÁ VINCULADOS
    # ==============================
    ids_vinculados = [a.idmatricula for a in alunos_passeio]

    # ==============================
    # ALUNOS DISPONÍVEIS
    # ==============================
    alunos = Ficha.query.filter(
        Ficha.situacao == "1",
        func.upper(Ficha.localpbm) == usuario.obm.upper(),
        Ficha.turnopbm != "RESERVA"
    ).order_by(Ficha.turnopbm, Ficha.nome).all()

    estrutura = {
        "MATUTINO": {"1": [], "2": [], "3": []},
        "VESPERTINO": {"1": [], "2": [], "3": []}
    }

    for aluno in alunos:

        if aluno.id in ids_vinculados:
            continue

        if not aluno.datanascimento:
            continue

        idade = hoje.year - aluno.datanascimento.year - (
            (hoje.month, hoje.day) <
            (aluno.datanascimento.month, aluno.datanascimento.day)
        )

        if 7 <= idade <= 9:
            pelotao = "1"
        elif 10 <= idade <= 11:
            pelotao = "2"
        elif 12 <= idade <= 14:
            pelotao = "3"
        else:
            continue

        estrutura[aluno.turnopbm][pelotao].append({
            "aluno": aluno,
            "idade": idade
        })

    return render_template(
        "gerenciar_passeio.html",
        passeio=passeio,
        alunos_passeio=alunos_passeio,
        estrutura=estrutura
    )

@main.route("/upload_foto/<int:id>", methods=["POST"])
def upload_foto(id):

    ficha = Ficha.query.get_or_404(id)

    if "foto" not in request.files:
        flash("Nenhum arquivo enviado.", "danger")
        return redirect(url_for("main.editar", id=id))

    arquivo = request.files["foto"]

    if arquivo.filename == "":
        flash("Arquivo inválido.", "danger")
        return redirect(url_for("main.editar", id=id))

    nome_seguro = secure_filename(arquivo.filename)

    caminho = os.path.join(current_app.root_path,
                           "static",
                           "images",
                           nome_seguro)

    arquivo.save(caminho)

    ficha.foto = nome_seguro
    db.session.commit()

    flash("Foto enviada com sucesso!", "success")

    return redirect(url_for("main.editar", id=id))
    
    
@main.route("/documento/termo_imagem/<int:id>")
def termo_imagem(id):
    ficha = Ficha.query.get_or_404(id)

    try:
        locale.setlocale(locale.LC_TIME, "pt_BR.UTF-8")
    except:
        pass

    data_extenso = datetime.now().strftime("%A, %d de %B de %Y")

    return render_template(
        "documentos/termo_imagem.html",
        ficha=ficha,
        data_extenso=data_extenso.capitalize()
    )

@main.route("/documento/certificado/<int:id>")
def certificado(id):
    ficha = Ficha.query.get_or_404(id)

    try:
        locale.setlocale(locale.LC_TIME, "pt_BR.UTF-8")
    except:
        pass

    data_extenso = datetime.now().strftime("%A, %d de %B de %Y")

    ano_inicio = ficha.dataregistro.year if ficha.dataregistro else ""
    ano_fim = ficha.dataalteracao.year if ficha.dataalteracao else datetime.now().year

    return render_template(
        "documentos/certificado.html",
        ficha=ficha,
        data_extenso=data_extenso.capitalize(),
        ano_inicio=ano_inicio,
        ano_fim=ano_fim
    )

@main.route("/documento/baixa_renda/<int:id>")
def baixa_renda(id):
    ficha = Ficha.query.get_or_404(id)

    # Data por extenso igual ao PHP
    try:
        locale.setlocale(locale.LC_TIME, "pt_BR.UTF-8")
    except:
        pass

    data_extenso = datetime.now().strftime("%A, %d de %B de %Y")

    return render_template(
        "documentos/baixa_renda.html",
        ficha=ficha,
        data_extenso=data_extenso.capitalize()
    )

@main.route("/documento/certificado_promocao/<int:id>")
def certificado_promocao(id):
    ficha = Ficha.query.get_or_404(id)

    try:
        locale.setlocale(locale.LC_TIME, "pt_BR.UTF-8")
    except:
        pass

    data_extenso = datetime.now().strftime("%A, %d de %B de %Y")

    return render_template(
        "documentos/certificado_promocao.html",
        ficha=ficha,
        data_extenso=data_extenso.capitalize()
    )

@main.route("/documento/declaracao_jovem_candango/<int:id>")
def declaracao_jovem_candango(id):
    ficha = Ficha.query.get_or_404(id)

    try:
        locale.setlocale(locale.LC_TIME, "pt_BR.UTF-8")
    except:
        pass

    data_extenso = datetime.now().strftime("%d de %B de %Y")

    return render_template(
        "documentos/declaracao_jovem_candango.html",
        ficha=ficha,
        data_extenso=data_extenso
    )

@main.route("/documento/carteirinha/<int:id>")
def carteirinha(id):
    ficha = Ficha.query.get_or_404(id)
    return render_template("documentos/carteirinha.html", ficha=ficha)

@main.route("/documento/declaracao_participacao/<int:id>")
def declaracao_participacao(id):
    ficha = Ficha.query.get_or_404(id)

    try:
        locale.setlocale(locale.LC_TIME, "pt_BR.UTF-8")
    except:
        pass

    data_extenso = datetime.now().strftime("%A, %d de %B de %Y")

    return render_template(
        "documentos/declaracao_participacao.html",
        ficha=ficha,
        data_extenso=data_extenso
    ) 
    

@main.route("/documento/declaracao_pais/<int:id>", methods=["GET", "POST"])
def declaracao_pais(id):

    ficha = Ficha.query.get_or_404(id)

    from datetime import datetime
    import locale

    try:
        locale.setlocale(locale.LC_TIME, "pt_BR.UTF-8")
    except:
        pass

    if request.method == "POST":
        nome = request.form.get("nome")
        cpf = request.form.get("cpf")
        periodo = request.form.get("periodo")
        hora_inicio = request.form.get("hora_inicio")
        hora_fim = request.form.get("hora_fim")
        texto = request.form.get("texto")

        data_extenso = datetime.now().strftime("%A, %d de %B de %Y")

        return render_template(
            "documentos/declaracao_comparecimento_print.html",
            nome=nome,
            cpf=cpf,
            periodo=periodo,
            hora_inicio=hora_inicio,
            hora_fim=hora_fim,
            texto=texto,
            data_extenso=data_extenso
        )

    return render_template(
        "documentos/declaracao_comparecimento_form.html",
        ficha=ficha
    )
    
@main.route("/documento/autorizacao_passeio/<int:idpasseio>")
@login_required
def autorizacao_passeio(idpasseio):

    passeio = Passeio.query.get_or_404(idpasseio)

    alunos = db.session.execute(text("""
        SELECT f.nome
        FROM bdpbm.passeio_alunos pa
        JOIN bdpbm.ficha f ON f.idmatricula = pa.idmatricula
        WHERE pa.idpasseio = :id
        ORDER BY f.nome
    """), {"id": idpasseio}).fetchall()

    return render_template(
        "documentos/autorizacao_passeio.html",
        passeio=passeio,
        alunos=alunos
    )
    
@main.route("/inscricao", methods=["GET"])
def inscricao():

    # buscar OBMs existentes no banco
    obms = db.session.execute(text("""
        SELECT DISTINCT localpbm
        FROM bdpbm.ficha
        WHERE localpbm IS NOT NULL
        ORDER BY localpbm
    """)).fetchall()

    lista_obms = [o.localpbm for o in obms]

    return render_template(
        "index.html",
        usuario=None,
        externo=True,
        obms=lista_obms
    )    
    
@main.route("/estatisticas-sipros")
def estatisticas_sipros():
    return "<h2>Relatórios SIPROS</h2>"

@main.route("/reserva-geral")
def reserva_geral():
    return "<h2>Reservas Geral</h2>"

@main.route("/chamada-geral")
def chamada_geral():
    return "<h2>Chamada Geral</h2>"

@main.route("/lista-pba")
def lista_pba():
    return "<h2>Lista PBA</h2>"

@main.route("/dashboard-estatisticas")
def dashboard_estatisticas():
    return "<h2>Dashboard Estatísticas</h2>"

@main.route("/usuarios-online")
def usuarios_online():
    return "<h2>Usuários Online</h2>"

@main.route("/usuarios-externos")
def usuarios_externos():
    return "<h2>Usuários Externos</h2>"

@main.route("/gerenciar-usuarios", methods=["GET", "POST"])
@login_required
def gerenciar_usuarios():

    # 🔐 Somente administrador (igual PHP nivel >= 1)
    if current_user.nivel < 1:
        return redirect(url_for("main.login"))

    # ==========================================
    # PRÓXIMO NÍVEL AUTOMÁTICO (igual PHP)
    # ==========================================
    max_nivel = db.session.execute(text("""
        SELECT MAX(nivel) FROM bdpbm.senha
    """)).scalar()

    proximo_nivel = (max_nivel or 0) + 1

    # ==========================================
    # ADICIONAR / EDITAR USUÁRIO
    # ==========================================
    if "submit" in request.form:

        idsenha = request.form.get("idsenha")
        nome = request.form.get("nome")
        usuario = request.form.get("usuario")
        obm = request.form.get("obm")
        nivel = request.form.get("nivel")
        funcao = request.form.get("funcao")
        status = request.form.get("status")
        senha = request.form.get("senha")

        # 🔥 tratar nível "outros"
        if nivel == "outros":
            nivel = proximo_nivel

        if not nivel:
            nivel = 2

        if idsenha:  # UPDATE

            if senha:
                import hashlib
                senha_md5 = hashlib.md5(senha.encode()).hexdigest()

                db.session.execute(text("""
                    UPDATE bdpbm.senha
                    SET nome = :nome,
                        usuario = :usuario,
                        obm = :obm,
                        nivel = :nivel,
                        funcao = :funcao,
                        status = :status,
                        senha = :senha,
                        dataatualizacao = NOW(),
                        respalteracao = :resp
                    WHERE idsenha = :id
                """), {
                    "nome": nome,
                    "usuario": usuario,
                    "obm": obm,
                    "nivel": nivel,
                    "funcao": funcao,
                    "status": status,
                    "senha": senha_md5,
                    "resp": current_user.idsenha,
                    "id": idsenha
                })

            else:
                db.session.execute(text("""
                    UPDATE bdpbm.senha
                    SET nome = :nome,
                        usuario = :usuario,
                        obm = :obm,
                        nivel = :nivel,
                        funcao = :funcao,
                        status = :status,
                        dataatualizacao = NOW(),
                        respalteracao = :resp
                    WHERE idsenha = :id
                """), {
                    "nome": nome,
                    "usuario": usuario,
                    "obm": obm,
                    "nivel": nivel,
                    "funcao": funcao,
                    "status": status,
                    "resp": current_user.idsenha,
                    "id": idsenha
                })

        else:  # INSERT

            import hashlib

            senha_final = senha if senha else "123456"
            senha_md5 = hashlib.md5(senha_final.encode()).hexdigest()

            db.session.execute(text("""
                INSERT INTO bdpbm.senha
                (nome, usuario, obm, nivel, funcao, status, senha, data, respalteracao)
                VALUES
                (:nome, :usuario, :obm, :nivel, :funcao, :status, :senha, NOW(), :resp)
            """), {
                "nome": nome,
                "usuario": usuario,
                "obm": obm,
                "nivel": nivel,
                "funcao": funcao,
                "status": True if status == "true" else False,
                "senha": senha_md5,
                "resp": current_user.idsenha
            })

        db.session.commit()
        return redirect(url_for("main.gerenciar_usuarios"))

    # ==========================================
    # EXCLUIR USUÁRIO
    # ==========================================
    if "delete" in request.form:
        idsenha = request.form.get("idsenha")

        db.session.execute(text("""
            DELETE FROM bdpbm.senha
            WHERE idsenha = :id
        """), {"id": idsenha})

        db.session.commit()
        return redirect(url_for("main.gerenciar_usuarios"))

    # ==========================================
    # ADICIONAR UNIDADE
    # ==========================================
    if "add_unit" in request.form:

        db.session.execute(text("""
            INSERT INTO bdpbm.tb_unidades
            (unidade, endereco, telefone)
            VALUES
            (:unidade, :endereco, :telefone)
        """), {
            "unidade": request.form.get("unidade"),
            "endereco": request.form.get("endereco"),
            "telefone": request.form.get("telefone")
        })

        db.session.commit()
        return redirect(url_for("main.gerenciar_usuarios"))

    # ==========================================
    # EXCLUIR UNIDADE
    # ==========================================
    if "delete_unit" in request.form:

        db.session.execute(text("""
            DELETE FROM bdpbm.tb_unidades
            WHERE id = :id
        """), {"id": request.form.get("id_unidade")})

        db.session.commit()
        return redirect(url_for("main.gerenciar_usuarios"))

    # ==========================================
    # BUSCAR USUÁRIO PARA EDITAR
    # ==========================================
    editUser = None
    if request.args.get("edit"):
        editUser = db.session.execute(text("""
            SELECT * FROM bdpbm.senha
            WHERE idsenha = :id
        """), {"id": request.args.get("edit")}).fetchone()

    # ==========================================
    # LISTAGENS
    # ==========================================
    usuarios = db.session.execute(text("""
        SELECT *
        FROM bdpbm.senha
        WHERE nivel <> 4
        AND status = true
        ORDER BY nome
    """)).fetchall()

    unidades_raw = db.session.execute(text("""
        SELECT nome_unidade
        FROM bdpbm.tb_unidades
        ORDER BY nome_unidade
    """)).fetchall()

    unidades = [u[0] for u in unidades_raw]

    # ==========================================
    # ESTATÍSTICAS
    # ==========================================
    stats_obm = db.session.execute(text("""
        SELECT obm, COUNT(*) as total
        FROM bdpbm.senha
        WHERE status = true
        GROUP BY obm
    """)).fetchall()

    stats_sexo = db.session.execute(text("""
        SELECT sexo, COUNT(*) as total
        FROM bdpbm.senha
        WHERE status = true
        GROUP BY sexo
    """)).fetchall()

    stats_funcao = db.session.execute(text("""
        SELECT funcao, COUNT(*) as total
        FROM bdpbm.senha
        WHERE status = true
        AND funcao IS NOT NULL
        AND funcao <> ''
        GROUP BY funcao
        ORDER BY funcao
    """)).mappings().all()

    return render_template(
        "gerenciar_usuarios.html",
        usuarios=usuarios,
        unidades=unidades,
        editUser=editUser,
        stats_obm=stats_obm,
        stats_sexo=stats_sexo,
        stats_funcao=stats_funcao,
        proximo_nivel=proximo_nivel
    )

@main.route("/lanches")
def lanches():
    return "<h2>Lanches</h2>"    