"""Exceptions propres au projet (une erreur métier = un message clair)."""


class VeilleError(Exception):
    """Erreur de base du projet."""


class ConfigError(VeilleError):
    """Configuration absente ou invalide."""


class DataError(VeilleError):
    """Fichier de données (candidats / analyse) absent ou mal formé."""


class ReportError(VeilleError):
    """Le rapport généré ne respecte pas le format attendu."""
