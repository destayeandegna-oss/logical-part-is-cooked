#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from pathlib import Path
import pprint

def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bb_eams.settings')

    # Add the bb_eams directory to sys.path so 'apps' can be imported
    sys.path.append(str(Path(__file__).resolve().parent / 'bb_eams'))

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    # Fix for Djongo compatibility with Django 4.0+
    from django.db.backends.base.base import BaseDatabaseWrapper
    BaseDatabaseWrapper.__bool__ = lambda self: True

    # Fix for packages importing 'url' from 'django.conf.urls' (removed in Django 4.0)
    import django.conf.urls
    from django.urls import re_path
    django.conf.urls.url = re_path
    
    pprint.pp(sys.path)

    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()