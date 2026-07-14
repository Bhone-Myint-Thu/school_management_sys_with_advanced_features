from pathlib import Path

from flask import Flask
from flask_login import current_user

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

    from .models import Notice, SystemSetting, User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    @app.context_processor
    def inject_system_settings():
        try:
            settings = SystemSetting.current()
        except Exception:
            settings = SystemSetting.defaults()
        notifications = []
        unread_notification_count = 0
        if current_user.is_authenticated:
            unread_notification_count = sum(1 for message in current_user.received_messages if not message.is_read)
            notifications.extend(
                {
                    "title": message.subject,
                    "body": f"From {message.sender.display_name}",
                    "when": message.sent_at.strftime("%Y-%m-%d"),
                    "unread": not message.is_read,
                }
                for message in sorted(current_user.received_messages, key=lambda row: row.sent_at, reverse=True)[:3]
            )
            audience_map = {
                "admin": ["all"],
                "headmaster": ["teachers", "parents", "all"],
                "dean": ["teachers", "parents", "all"],
                "teacher": ["teachers", "parents", "all"],
                "parent": ["parents", "all"],
                "student": ["all"],
            }
            try:
                notices = (
                    Notice.query.filter(Notice.status == "approved", Notice.audience.in_(audience_map.get(current_user.role, ["all"])))
                    .order_by(Notice.approved_at.desc(), Notice.created_at.desc())
                    .limit(3)
                    .all()
                )
                notifications.extend(
                    {
                        "title": notice.title,
                        "body": notice.audience.title(),
                        "when": (notice.approved_at or notice.created_at).strftime("%Y-%m-%d"),
                        "unread": False,
                    }
                    for notice in notices
                )
            except Exception:
                pass
        return {
            "system_settings": settings,
            "top_notifications": notifications[:5],
            "unread_notification_count": unread_notification_count,
        }

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
