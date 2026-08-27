from flask import Blueprint, jsonify
from app.services.metrics_service import MetricsService

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/summary')
def summary():
    metrics = MetricsService.get_dashboard_summary()
    return jsonify(metrics)


@dashboard_bp.route('/funnel')
def funnel():
    funnel_data = MetricsService.get_recovery_funnel()
    return jsonify(funnel_data)


@dashboard_bp.route('/failures')
def failures():
    distribution = MetricsService.get_failure_distribution()
    return jsonify(distribution)
