"""
API routes for the HR system.
Handles JSON responses for the chatbot and interactive elements.
"""

from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
from models import User, LeaveRequest, TrainingEnrollment, TeachingUnit
from chatbot import chatbot
import json

api_bp = Blueprint('api', __name__, url_prefix='/api')

# Chatbot API endpoints
@api_bp.route('/chatbot/message', methods=['POST'])
@login_required
def chatbot_message():
    """Process a message sent to the chatbot"""
    try:
        # Get message from request
        data = request.get_json()
        
        # Ensure message is provided
        if not data or 'message' not in data:
            return jsonify({
                "status": "error",
                "message": "No message provided"
            }), 400
            
        # Get response from chatbot
        user_message = data['message']
        response = chatbot.get_response(user_message, current_user.id)
        
        return jsonify(response)
    except Exception as e:
        current_app.logger.error(f"Chatbot error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "An error occurred processing your request"
        }), 500

@api_bp.route('/chatbot/reset', methods=['POST'])
@login_required
def chatbot_reset():
    """Reset the chatbot conversation"""
    try:
        response = chatbot.reset_conversation(current_user.id)
        return jsonify(response)
    except Exception as e:
        current_app.logger.error(f"Chatbot reset error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "An error occurred resetting the conversation"
        }), 500

@api_bp.route('/chatbot/user-info/<info_type>', methods=['GET'])
@login_required
def chatbot_user_info(info_type):
    """Get user-specific information for the chatbot"""
    try:
        response = chatbot.get_user_info(current_user.id, info_type)
        return jsonify(response)
    except Exception as e:
        current_app.logger.error(f"Chatbot user info error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"An error occurred getting {info_type} information"
        }), 500

@api_bp.route('/api/users/search', methods=['GET'])
@login_required
def search_users():
    """API endpoint to search for users"""
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify([])
        
    # Search for users matching the query
    users = User.query.filter(
        (User.username.ilike(f'%{query}%')) | 
        (User.email.ilike(f'%{query}%'))
    ).limit(10).all()
    
    # Format results
    results = [
        {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'display_name': user.get_display_name(),
            'department': user.department
        }
        for user in users
    ]
    
    return jsonify(results)

@api_bp.route('/api/leave-requests/user/<int:user_id>/status', methods=['GET'])
@login_required
def get_leave_status(user_id):
    """Get leave request status statistics for a user"""
    if user_id != current_user.id and not (current_user.is_hr() or current_user.is_admin()):
        return jsonify({'status': 'error', 'message': 'Not authorized'})
    
    # Count leave requests by status
    pending = LeaveRequest.query.filter_by(employee_id=user_id, status='pending').count()
    approved = LeaveRequest.query.filter_by(employee_id=user_id, status='approved').count()
    denied = LeaveRequest.query.filter_by(employee_id=user_id, status='denied').count()
    
    return jsonify({
        'pending': pending,
        'approved': approved,
        'denied': denied,
        'total': pending + approved + denied
    })

@api_bp.route('/api/teaching-units/user/<int:user_id>/stats', methods=['GET'])
@login_required
def get_teaching_stats(user_id):
    """Get teaching unit statistics for a user"""
    if user_id != current_user.id and not (current_user.is_hr() or current_user.is_admin()):
        return jsonify({'status': 'error', 'message': 'Not authorized'})
    
    # Get teaching units
    active_units = TeachingUnit.query.filter_by(employee_id=user_id, status='active').all()
    
    # Calculate statistics
    total_units = len(active_units)
    total_hours = sum(unit.hours_per_week for unit in active_units)
    attendance_rates = [unit.attendance_rate for unit in active_units]
    avg_attendance = sum(attendance_rates) / len(attendance_rates) if attendance_rates else 0
    
    return jsonify({
        'total_units': total_units,
        'total_hours': total_hours,
        'avg_attendance': avg_attendance
    })
