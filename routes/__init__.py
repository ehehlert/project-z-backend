from .user_routes import user_bp
from .device_routes import device_bp
from .reporting_routes import reporting_bp

def register_routes(app):
        app.register_blueprint(user_bp)
        app.register_blueprint(device_bp)
        app.register_blueprint(reporting_bp)