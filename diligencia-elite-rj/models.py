from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Diligencia(db.Model):
    __tablename__ = 'diligencias'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, default='Nova diligência')
    process_number = db.Column(db.String(100), unique=True, nullable=False)
    responsavel = db.Column(db.String(255), default='')
    region = db.Column(db.String(100), default='Não informado')
    municipio = db.Column(db.String(255), default='')
    comarca = db.Column(db.String(255), default='')
    lat = db.Column(db.Float, default=-22.9068)
    lng = db.Column(db.Float, default=-43.1729)
    status = db.Column(db.String(50), default='Pendente')
    resumo = db.Column(db.Text, default='')
    processos = db.Column(db.Integer, default=1)
    valor_alvara = db.Column(db.Float)
    valor_total = db.Column(db.Float)
    valor_causa = db.Column(db.Float)
    roteiro_estrategico = db.Column(db.Text, default='')
    modalidade_diligencia = db.Column(db.String(255), default='Não informado')
    distancia_roteiro = db.Column(db.Float)
    preco_gasolina = db.Column(db.Float)
    preco_aluguel_carro = db.Column(db.Float)
    modus_operandi = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'process_number': self.process_number,
            'responsavel': self.responsavel,
            'region': self.region,
            'municipio': self.municipio,
            'comarca': self.comarca,
            'lat': self.lat,
            'lng': self.lng,
            'status': self.status,
            'resumo': self.resumo,
            'processos': self.processos,
            'valor_alvara': self.valor_alvara,
            'valor_total': self.valor_total,
            'valor_causa': self.valor_causa,
            'roteiro_estrategico': self.roteiro_estrategico,
            'modalidade_diligencia': self.modalidade_diligencia,
            'distancia_roteiro': self.distancia_roteiro,
            'preco_gasolina': self.preco_gasolina,
            'preco_aluguel_carro': self.preco_aluguel_carro,
            'modus_operandi': self.modus_operandi,
        }


class Processo(db.Model):
    __tablename__ = 'processos'
    
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(100), unique=True, nullable=False)
    status = db.Column(db.String(50), default='Pendente')
    region = db.Column(db.String(100), default='Metropolitana')
    municipio = db.Column(db.String(255), default='')
    comarca = db.Column(db.String(255), default='')
    responsavel = db.Column(db.String(255), default='')
    urgencia = db.Column(db.String(50), default='Pendente')
    resumo = db.Column(db.Text, default='')
    valor_alvara = db.Column(db.Float)
    valor_total = db.Column(db.Float)
    valor_causa = db.Column(db.Float)
    roteiro_estrategico = db.Column(db.Text, default='')
    modalidade_diligencia = db.Column(db.String(255), default='Não informado')
    distancia_roteiro = db.Column(db.Float)
    preco_gasolina = db.Column(db.Float)
    preco_aluguel_carro = db.Column(db.Float)
    modus_operandi = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'numero': self.numero,
            'status': self.status,
            'region': self.region,
            'municipio': self.municipio,
            'comarca': self.comarca,
            'responsavel': self.responsavel,
            'urgencia': self.urgencia,
            'resumo': self.resumo,
            'valor_alvara': self.valor_alvara,
            'valor_total': self.valor_total,
            'valor_causa': self.valor_causa,
            'roteiro_estrategico': self.roteiro_estrategico,
            'modalidade_diligencia': self.modalidade_diligencia,
            'distancia_roteiro': self.distancia_roteiro,
            'preco_gasolina': self.preco_gasolina,
            'preco_aluguel_carro': self.preco_aluguel_carro,
            'modus_operandi': self.modus_operandi,
        }


class ReportHistory(db.Model):
    __tablename__ = 'report_history'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    report_data = db.Column(db.Text)

    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'report_data': self.report_data,
        }
