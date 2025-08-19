from .user_routes import user_bp
from .device_routes import device_bp
from .reporting_routes import reporting_bp
from .auth_routes import auth_bp
from .graph_routes import graph_bp

def register_routes(app):
        app.register_blueprint(auth_bp)
        app.register_blueprint(user_bp)
        app.register_blueprint(device_bp)
        app.register_blueprint(reporting_bp)
        app.register_blueprint(graph_bp)