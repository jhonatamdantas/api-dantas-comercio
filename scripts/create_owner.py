from getpass import getpass
from sqlmodel import Session, select

from app.db.session import engine, create_table
from app.models import user
from app.models.user import Role
from app.core.security import hash_password

def main():
    create_table()
    with Session(engine) as session:
        existing = session.exec(select(user.User)).first()
        if existing:
            print("Usuário já existente")
            return
        email = input("E-mail: ")
        password = getpass("Senha: ")

        user_create = user.User(role=Role.owner, hashed_password=hash_password(password), email=email)
        session.add(user_create)
        session.commit()
        print("Usuário criado com sucesso")

if __name__ == "__main__":
    main()