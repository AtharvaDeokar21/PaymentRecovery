from flask import Blueprint, jsonify, request

agent_bp = Blueprint('agent', __name__)


@agent_bp.route('/status')
def agent_status():
    return jsonify({'status': 'ready', 'model': 'gemini-2.5-flash'})
