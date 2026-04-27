from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Cette table permet de définir les matières (Ex: Math, Java)
class Matiere(Base):
    __tablename__ = 'matiere'
    id = Column(Integer, primary_key=True)
    nom = Column(String(100))
    coefficient = Column(Float)

# Cette table sert à enregistrer les notes des élèves
class Note(Base):
    __tablename__ = 'note'
    id = Column(Integer, primary_key=True)
    valeur = Column(Float)
    date_evaluation = Column(Date)
    id_etudiant = Column(Integer, ForeignKey('utilisateur.id'))
    id_matiere = Column(Integer, ForeignKey('matiere.id'))

# Cette table sert pour le suivi des absences
class Absence(Base):
    __tablename__ = 'absence'
    id = Column(Integer, primary_key=True)
    date = Column(Date)
    justifiee = Column(Boolean, default=False)
    id_etudiant = Column(Integer, ForeignKey('utilisateur.id'))
