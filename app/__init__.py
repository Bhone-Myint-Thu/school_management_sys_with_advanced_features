from pathlib import Path

from flask import Flask

from config import Config

from .extensions import csrf, db, login_manager, mail


def create_app(config_object=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_object)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "warning"

    from .admin.routes import bp as admin_bp
    from .auth.routes import bp as auth_bp
    from .main.routes import bp as main_bp
    from .parent.routes import bp as parent_bp
    from .student.routes import bp as student_bp
    from .teacher.routes import bp as teacher_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(teacher_bp)
    app.register_blueprint(parent_bp)
    app.register_blueprint(student_bp)

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    register_commands(app)
    return app


def register_commands(app):
    @app.cli.command("init-db")
    def init_db():
        from .seed import seed_demo_data

        db.drop_all()
        db.create_all()
        seed_demo_data()
        print("Database initialised with fictitious demo data.")
