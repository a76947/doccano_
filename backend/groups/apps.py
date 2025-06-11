from django.apps import AppConfig
import os

class GroupsConfig(AppConfig):
    name = 'groups'
    path = os.path.dirname(os.path.abspath(__file__))