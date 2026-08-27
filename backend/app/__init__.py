from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()


def create_app():
    app = Flask(__name__)
    app.config.from_object('app.config.Config')

    CORS(app, origins=[app.config.get('FRONTEND_URL', 'http://localhost:3000')])

    db.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    from app.routes.health import health_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.payments import payments_bp
    from app.routes.recovery import recovery_bp
    from app.routes.agent import agent_bp
    from app.routes.policies import policies_bp
    from app.routes.audit import audit_bp
    from app.routes.razorpay import razorpay_bp
    from app.routes.demo import demo_bp
    from app.routes.analytics import analytics_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(payments_bp, url_prefix='/api/payments')
    app.register_blueprint(recovery_bp, url_prefix='/api/recovery')
    app.register_blueprint(agent_bp, url_prefix='/api/agent')
    app.register_blueprint(policies_bp, url_prefix='/api/policies')
    app.register_blueprint(audit_bp, url_prefix='/api/audit')
    app.register_blueprint(razorpay_bp, url_prefix='/api/razorpay')
    app.register_blueprint(demo_bp, url_prefix='/api/demo')
    app.register_blueprint(analytics_bp, url_prefix='/api/analytics')

    with app.app_context():
        db.create_all()

    return app
