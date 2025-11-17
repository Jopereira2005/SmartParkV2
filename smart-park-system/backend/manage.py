#!/usr/bin/env python
import os
import sys


def main():
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE",
        os.getenv("DJANGO_SETTINGS_MODULE", "smartpark.settings.dev"),
    )
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
