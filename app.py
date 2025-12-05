"""
Event Calendar Flask Application

This is the main application file using Flask factory pattern with Blueprints.
"""

from flask import Flask

# Import blueprints
from routes.web_routes import web_bp
from routes.api_routes import api_bp


def create_app(config_name='default'):
    """
    Application factory function.
    
    Args:
        config_name: Configuration name (default, testing, production)
        
    Returns:
        Flask application instance
    """
    app = Flask(__name__)
    
    # Load configuration
    app.secret_key = 'event-calendar'  # TODO: Move to environment variable
    
    # Register blueprints
    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp)
    
    return app


# Create the application instance
app = create_app()


if __name__ == '__main__':
    app.run(debug=True)
