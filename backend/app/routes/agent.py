from flask import Blueprint, jsonify, request, current_app
from app.utils.logging import get_logger

agent_bp = Blueprint('agent', __name__)
logger = get_logger('agent_routes')


@agent_bp.route('/status')
def agent_status():
    """Report agent status and configuration."""
    gemini_key = current_app.config.get('GEMINI_API_KEY', '')
    is_configured = bool(gemini_key)

    # Check if ML predictor is available
    from app.ml.predictor import get_predictor
    predictor = get_predictor()
    ml_available = predictor.model is not None

    status = {
        'status': 'ready' if is_configured else 'fallback',
        'model': 'gemini-3.6-flash',
        'provider': 'Google Gemini',
        'configured': is_configured,
        'fallback_available': ml_available,
        'ml_model_version': predictor.model_version if predictor.model else 'unavailable',
    }

    logger.info(f"Agent status: {status}")
    return jsonify(status)
