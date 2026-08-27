from flask import Blueprint, jsonify, current_app

razorpay_bp = Blueprint('razorpay', __name__)


@razorpay_bp.route('/status')
def razorpay_status():
    mode = current_app.config.get('RAZORPAY_MODE', 'simulation')
    has_keys = bool(current_app.config.get('RAZORPAY_KEY_ID'))
    return jsonify({
        'mode': mode,
        'configured': has_keys,
        'status': 'connected' if has_keys else 'simulation_only',
    })
