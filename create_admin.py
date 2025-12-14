from werkzeug.security import generate_password_hash
from flask_app import app
from models import db, Admin
import argparse
import getpass
import sys

# Опционально: можно прописать логин/пароль прямо в этом файле.
# Установите значения здесь, если хотите автоматизировать создание администратора
# Пример:
# ADMIN_LOGIN = 'admin'
# ADMIN_PASSWORD = 'SuperSecret'
ADMIN_LOGIN = '-'
ADMIN_PASSWORD = '-'


def parse_args():
    p = argparse.ArgumentParser(description='Create or update an admin user')
    p.add_argument('--login', '-l', help='Admin login')
    p.add_argument('--password', '-p', help='Admin password (use with care)')
    return p.parse_args()


def main():
    args = parse_args()
    # Priority for credentials:
    # 1) hardcoded ADMIN_LOGIN / ADMIN_PASSWORD in this file
    # 2) command-line args
    # 3) credential files (admin_credentials.txt / create_admin.txt)
    login = ADMIN_LOGIN or args.login or None
    password = ADMIN_PASSWORD or args.password or None

    # Support reading credentials from a credentials file for automated runs.
    # Try files in order; preferred filename is 'admin_credentials.txt'.
    # File format: first non-empty non-comment line = login, second = password.
    cred_files = ['admin_credentials.txt', 'create_admin.txt']
    try:
        if not login or not password:
            from pathlib import Path
            for cred_file in cred_files:
                p = Path(cred_file)
                if not p.exists():
                    continue
                lines = [l.strip() for l in p.read_text(encoding='utf-8').splitlines() if l.strip() and not l.strip().startswith('#')]
                if len(lines) >= 2:
                    file_login, file_password = lines[0], lines[1]
                    if not login:
                        login = file_login
                    if not password:
                        password = file_password
                    break
    except Exception:
        # if reading file fails, continue to interactive/CLI flow
        pass

    if not login:
        login = input('Admin login: ').strip()
    if not login:
        print('Error: login is required', file=sys.stderr)
        sys.exit(2)

    if not password:
        password = getpass.getpass('Admin password: ')
        if not password:
            print('Error: password is required', file=sys.stderr)
            sys.exit(2)

    with app.app_context():
        try:
            existing_admin = Admin.query.filter_by(login=login).first()
            hashed = generate_password_hash(password)
            if existing_admin:
                existing_admin.password = hashed
                db.session.commit()
                print(f'Updated password for admin: {login}')
            else:
                admin = Admin(login=login, password=hashed)
                db.session.add(admin)
                db.session.commit()
                print(f'Created new admin: {login}')
        except Exception as e:
            db.session.rollback()
            print('Failed to create/update admin:', e, file=sys.stderr)
            sys.exit(1)


if __name__ == '__main__':
    main()