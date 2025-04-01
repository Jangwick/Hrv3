"""
School HR System Chatbot using Google Gemini API with user data integration
"""
import os
import json
from dotenv import load_dotenv
from google import genai
from flask_login import current_user
from models import db, User, EmployeeProfile, LeaveRequest, TrainingEnrollment, TrainingProgram

# Load environment variables
load_dotenv()

# Initialize Gemini API client
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

class HRChatbot:
    """School HR Assistant powered by Google Gemini API with user data integration"""
    
    def __init__(self):
        self.model_name = "gemini-2.0-flash"
        self.history = {}  # Store conversation history per user
        self.base_system_prompt = """
        You are an AI assistant for a School HR Management System. Your name is School HR Assistant.
        
        Provide helpful information about:
        - School policies and procedures for staff
        - Faculty and staff benefits and time off
        - Professional development and training programs
        - Academic calendar and school schedules
        - Employment contracts and teaching assignments
        
        Keep responses brief, professional, and helpful. If you don't know the answer,
        suggest contacting the school's HR department or administration directly. 
        Don't disclose confidential faculty/staff information or make specific promises 
        about benefits/policies that might vary by school.
        
        When asked about curriculum or student matters, explain that you're focused on 
        staff management issues, and suggest contacting the appropriate academic department.
        """
    
    def get_user_context(self, user_id):
        """Get personalized context for the current user"""
        try:
            # Get user info
            user = User.query.get(user_id)
            if not user:
                return {}
            
            # Get user profile
            profile = EmployeeProfile.query.filter_by(user_id=user_id).first()
            
            # Get pending leave requests
            pending_leaves = LeaveRequest.query.filter_by(
                employee_id=user_id, 
                status='pending'
            ).count()
            
            # Get upcoming trainings
            upcoming_trainings = TrainingEnrollment.query.filter_by(
                employee_id=user_id, 
                status='enrolled'
            ).join(TrainingEnrollment.training).filter(
                TrainingProgram.status.in_(['upcoming', 'in-progress'])
            ).count()
            
            # Get leave details for context
            leave_details = self.get_leave_details(user_id)
            
            # Create context object
            context = {
                "name": f"{profile.first_name} {profile.last_name}" if profile and profile.first_name else user.username,
                "username": user.username,
                "email": user.email,
                "department": user.department,
                "role": user.role,
                "position": profile.position if profile else None,
                "hire_date": profile.hire_date.strftime("%Y-%m-%d") if profile and profile.hire_date else None,
                "pending_leaves": pending_leaves,
                "upcoming_trainings": upcoming_trainings,
                "leave_details": leave_details
            }
            
            return context
        except Exception as e:
            print(f"Error getting user context: {e}")
            return {}
    
    def get_leave_details(self, user_id):
        """Get detailed information about a user's leave requests"""
        try:
            # Get all leave requests for the user (limit to recent ones to avoid context size issues)
            leave_requests = LeaveRequest.query.filter_by(employee_id=user_id).order_by(
                LeaveRequest.created_at.desc()
            ).limit(5).all()
            
            leave_details = []
            for leave in leave_requests:
                leave_details.append({
                    "id": leave.id,
                    "leave_type": leave.leave_type,
                    "start_date": leave.start_date.strftime("%Y-%m-%d"),
                    "end_date": leave.end_date.strftime("%Y-%m-%d"),
                    "duration_days": leave.duration_days,
                    "reason": leave.reason,
                    "status": leave.status,
                    "submitted_on": leave.created_at.strftime("%Y-%m-%d"),
                    "approved_by": leave.approved_by.username if leave.approved_by else None,
                    "approval_date": leave.approved_at.strftime("%Y-%m-%d") if leave.approved_at else None,
                    "rejection_reason": leave.rejection_reason
                })
            
            return leave_details
        except Exception as e:
            print(f"Error getting leave details: {e}")
            return []
    
    def get_personalized_system_prompt(self, user_id):
        """Create a personalized system prompt with user context"""
        user_context = self.get_user_context(user_id)
        
        if not user_context:
            return self.base_system_prompt
            
        context_prompt = f"""
        Currently assisting: {user_context.get('name', 'Unknown User')}
        Department: {user_context.get('department', 'Unknown')}
        Position: {user_context.get('position', 'Unknown')}
        Role: {user_context.get('role', 'faculty/staff')}
        
        User has {user_context.get('pending_leaves', 0)} pending leave requests.
        User has {user_context.get('upcoming_trainings', 0)} upcoming professional development enrollments.
        
        Leave request details:
        """
        
        # Add leave request details if available
        if user_context.get('leave_details'):
            for i, leave in enumerate(user_context.get('leave_details')):
                context_prompt += f"""
                Leave #{i+1}:
                - Type: {leave.get('leave_type', 'Unknown').title()}
                - Dates: {leave.get('start_date')} to {leave.get('end_date')} ({leave.get('duration_days')} days)
                - Status: {leave.get('status', 'Unknown').title()}
                - Reason: {leave.get('reason', 'Not provided')}
                - Submitted: {leave.get('submitted_on')}
                """
                if leave.get('status') == 'approved':
                    context_prompt += f"- Approved by: {leave.get('approved_by')} on {leave.get('approval_date')}\n"
                elif leave.get('status') == 'rejected':
                    context_prompt += f"- Rejected reason: {leave.get('rejection_reason', 'Not provided')}\n"
        
        context_prompt += """
        When the user asks about their leave requests or specific leave details, use this context to provide accurate and personalized responses.
        Do not share this specific information unless directly asked about it.
        """
        
        return self.base_system_prompt + context_prompt
    
    def get_response(self, user_message, user_id):
        """Get a response from the Gemini model for the user message"""
        try:
            # Initialize history for user if not exists
            if user_id not in self.history:
                self.history[user_id] = []
                
            # Get personalized system prompt
            system_prompt = self.get_personalized_system_prompt(user_id)
            
            # Add user message to history
            self.history[user_id].append({"role": "user", "parts": [{"text": user_message}]})
            
            # Prepare the conversation history with system prompt
            conversation = [{"role": "model", "parts": [{"text": system_prompt}]}]
            conversation.extend(self.history[user_id])
            
            # Generate response using the client
            response = client.models.generate_content(
                model=self.model_name,
                contents=conversation
            )
            
            # Extract the text from the response
            response_text = response.text
            
            # Add model response to history
            self.history[user_id].append({"role": "model", "parts": [{"text": response_text}]})
            
            return {
                "status": "success",
                "message": response_text
            }
        except Exception as e:
            print(f"Gemini API error: {str(e)}")
            return {
                "status": "error",
                "message": "I'm having trouble connecting to my knowledge base. Please try again later."
            }
    
    def reset_conversation(self, user_id):
        """Reset the conversation history for a specific user"""
        if user_id in self.history:
            self.history[user_id] = []
        
        return {
            "status": "success",
            "message": "Conversation has been reset."
        }
    
    def get_user_info(self, user_id, info_type):
        """Get specific user information for predefined queries"""
        context = self.get_user_context(user_id)
        
        if info_type == 'leave_balance':
            # This would ideally come from a dedicated leave_balance table
            # School-specific leave allocations
            return {
                "status": "success",
                "annual_leave": 15,
                "sick_leave": 12,
                "personal_leave": 3,
                "professional_days": 5,
                "used_annual": 3,
                "used_sick": 2,
                "used_personal": 1,
                "used_professional": 2
            }
            
        elif info_type == 'upcoming_trainings':
            # Get actual upcoming training data
            trainings = TrainingEnrollment.query.filter_by(employee_id=user_id).all()
            training_data = []
            
            for enrollment in trainings:
                training_data.append({
                    "title": enrollment.training.title,
                    "start_date": enrollment.training.start_date.strftime("%Y-%m-%d"),
                    "end_date": enrollment.training.end_date.strftime("%Y-%m-%d"),
                    "status": enrollment.status
                })
                
            return {
                "status": "success",
                "trainings": training_data
            }
            
        elif info_type == 'pending_leaves':
            # Get actual pending leave data
            leaves = LeaveRequest.query.filter_by(
                employee_id=user_id,
                status='pending'
            ).all()
            
            leave_data = []
            for leave in leaves:
                leave_data.append({
                    "leave_type": leave.leave_type,
                    "start_date": leave.start_date.strftime("%Y-%m-%d"),
                    "end_date": leave.end_date.strftime("%Y-%m-%d"),
                    "duration_days": leave.duration_days
                })
                
            return {
                "status": "success",
                "leaves": leave_data
            }
            
        elif info_type == 'leave_details':
            # Return detailed leave information in a structured format for tables
            leave_details = context.get('leave_details', [])
            
            # Define table columns for better frontend rendering
            columns = [
                {"id": "leave_type", "name": "Type", "width": "15%"},
                {"id": "date_range", "name": "Dates", "width": "20%"},
                {"id": "status", "name": "Status", "width": "15%"},
                {"id": "details", "name": "Details", "width": "50%"}
            ]
            
            # Format data for improved table display
            formatted_data = []
            for leave in leave_details:
                # Format dates range as a single field
                date_range = f"{leave.get('start_date')} to {leave.get('end_date')}"
                duration = f"{leave.get('duration_days')} days"
                
                # Create detail text with paragraph structure for better display
                details = f"Reason: {leave.get('reason')}<br>"
                details += f"Submitted: {leave.get('submitted_on')}"
                
                if leave.get('status') == 'approved' and leave.get('approved_by'):
                    details += f"<br><span class='text-success'>Approved by {leave.get('approved_by')} on {leave.get('approval_date')}</span>"
                
                if leave.get('status') == 'rejected':
                    rejection_reason = leave.get('rejection_reason') or 'No reason provided'
                    details += f"<br><span class='text-danger'>Rejected: {rejection_reason}</span>"
                
                # Add formatted row
                formatted_data.append({
                    "leave_type": leave.get('leave_type', '').capitalize(),
                    "date_range": f"{date_range}<br><small class='text-muted'>({duration})</small>",
                    "status": leave.get('status', '').capitalize(),
                    "status_class": self._get_status_class(leave.get('status')),
                    "details": details
                })
            
            return {
                "status": "success",
                "columns": columns,
                "leave_details": formatted_data,
                "count": len(formatted_data)
            }
            
        return {
            "status": "error",
            "message": "Information not available"
        }
    
    def _get_status_class(self, status):
        """Helper method to get CSS class for leave status"""
        if status == 'approved':
            return 'success'
        elif status == 'rejected':
            return 'danger'
        elif status == 'pending':
            return 'warning'
        else:
            return 'secondary'

# Create a singleton instance
chatbot = HRChatbot()
