from datetime import timedelta
from getpass import getpass

import typer
from sqlalchemy.orm import Session

from .core.security import create_access_token, get_password_hash
from .db.postgres import Base, SessionLocal, engine
from .models import User

app = typer.Typer(help="Management commands")


def _db() -> Session:
    Base.metadata.create_all(bind=engine)
    return SessionLocal()


def _require_user(db: Session, email: str) -> User:
    u = db.query(User).filter(User.email == email).first()
    if not u:
        typer.secho(f"User not found: {email}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    return u


def _prompt_password_twice() -> str:
    pw1 = getpass("Password: ")
    pw2 = getpass("Password (again): ")
    if pw1 != pw2:
        typer.secho("Error: passwords do not match.", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    if not pw1:
        typer.secho("Error: password cannot be empty.", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    return pw1


def _print_kv(title: str, data: dict[str, str]) -> None:
    print(f"\n{title}")
    print("-" * len(title))
    for k, v in data.items():
        print(f"{k:12}: {v}")
    print("")


def _print_table(rows: list[tuple[str, str]], headers=("Email", "Full name")) -> None:
    col1w = max(len(headers[0]), *(len(r[0]) for r in rows)) if rows else len(headers[0])
    col2w = max(len(headers[1]), *(len(r[1] or "") for r in rows)) if rows else len(headers[1])
    print(f"{headers[0]:<{col1w}}  {headers[1]:<{col2w}}")
    print(f"{'-'*col1w}  {'-'*col2w}")
    for r1, r2 in rows:
        print(f"{r1:<{col1w}}  {r2 or ''!s:<{col2w}}")
    print("")


@app.command("create-user")
def create_user(
    email: str = typer.Option(..., "--email", "-e", help="User email"),
    password: str | None = typer.Option(
        None, "--password", "-p", help="User password (prompt if omitted)"
    ),
    full_name: str = typer.Option("", "--full-name", "-n", help="Full name"),
):
    if not password:
        password = _prompt_password_twice()

    db = _db()
    try:
        exists = db.query(User).filter(User.email == email).first()
        if exists:
            typer.secho(f"User with email {email} already exists.", fg=typer.colors.YELLOW)
            raise typer.Exit(code=1)
        u = User(
            email=email, hashed_password=get_password_hash(password), full_name=full_name or ""
        )
        db.add(u)
        db.commit()
        typer.secho(f"Created user: {email}", fg=typer.colors.GREEN)
    finally:
        db.close()


@app.command("set-password")
def set_password(
    email: str = typer.Option(..., "--email", "-e", help="User email"),
    password: str | None = typer.Option(
        None, "--password", "-p", help="New password (prompt if omitted)"
    ),
):
    if not password:
        password = _prompt_password_twice()

    db = _db()
    try:
        u = _require_user(db, email)
        u.hashed_password = get_password_hash(password)
        db.add(u)
        db.commit()
        typer.secho(f"Updated password for {email}", fg=typer.colors.GREEN)
    finally:
        db.close()


@app.command("set-full-name")
def set_full_name(
    email: str = typer.Option(..., "--email", "-e", help="User email"),
    full_name: str = typer.Option(..., "--full-name", "-n", help="New full name"),
):
    db = _db()
    try:
        u = _require_user(db, email)
        u.full_name = full_name
        db.add(u)
        db.commit()
        typer.secho(f"Updated full name for {email}", fg=typer.colors.GREEN)
    finally:
        db.close()


@app.command("list-users")
def list_users(
    q: str | None = typer.Option(None, "--q", "-q", help="Filter by substring in email"),
    limit: int = typer.Option(100, "--limit", "-l", help="Max rows"),
):
    db = _db()
    try:
        qry = db.query(User)
        if q:
            like = f"%{q}%"
            qry = qry.filter(User.email.ilike(like))
        users = qry.order_by(User.email.asc()).limit(limit).all()
        rows = [(u.email, u.full_name or "") for u in users]
        _print_table(rows, headers=("Email", "Full name"))
        typer.echo(f"Total: {len(rows)}")
    finally:
        db.close()


@app.command("show-user")
def show_user(email: str = typer.Option(..., "--email", "-e", help="User email")):
    db = _db()
    try:
        u = _require_user(db, email)
        _print_kv("User", {"email": u.email, "full_name": u.full_name or ""})
    finally:
        db.close()


@app.command("delete-user")
def delete_user(
    email: str = typer.Option(..., "--email", "-e", help="User email"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
):
    if not yes and not typer.confirm(f"Delete user '{email}'?"):
        typer.echo("Aborted.")
        raise typer.Exit(code=1)

    db = _db()
    try:
        u = _require_user(db, email)
        db.delete(u)
        db.commit()
        typer.secho(f"Deleted user: {email}", fg=typer.colors.GREEN)
    finally:
        db.close()


@app.command("create-token")
def create_token(
    email: str = typer.Option(..., "--email", "-e", help="User email"),
    minutes: int | None = typer.Option(None, "--expires-min", "-m", help="Override expiry minutes"),
):
    db = _db()
    try:
        u = _require_user(db, email)
        expires = timedelta(minutes=minutes) if minutes else None
        token = create_access_token(subject=u.email, expires_delta=expires)
        typer.echo(token)
    finally:
        db.close()


if __name__ == "__main__":
    app()
