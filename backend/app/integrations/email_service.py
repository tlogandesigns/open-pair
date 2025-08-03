import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import os
from jinja2 import Template
from sqlalchemy.orm import Session
from app.models.database_models import Agent, OpenHouse, Listing, AgentRecommendation
from app.models.schemas import WeeklyRecommendations, OpenHouseWithRecommendations

class EmailService:
    """Email notification service for open house matchmaker"""
    
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.sender_email = os.getenv("SENDER_EMAIL", "noreply@openhouse.com")
        self.sender_password = os.getenv("SENDER_PASSWORD", "")
        self.sender_name = os.getenv("SENDER_NAME", "Open House Matchmaker")
    
    def send_email(self, to_email: str, subject: str, html_content: str, 
                   text_content: Optional[str] = None) -> Dict[str, Any]:
        """Send an email"""
        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.sender_name} <{self.sender_email}>"
            message["To"] = to_email
            
            # Add text version if provided
            if text_content:
                text_part = MIMEText(text_content, "plain")
                message.attach(text_part)
            
            # Add HTML version
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)
            
            # Create secure connection and send email
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                if self.sender_password:
                    server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, to_email, message.as_string())
            
            return {"success": True, "sent_at": datetime.now()}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def send_agent_recommendation_notification(self, open_house: OpenHouse, 
                                             recommended_agents: List[Dict[str, Any]], 
                                             db: Session) -> Dict[str, Any]:
        """Send notification about new agent recommendations"""
        listing = db.query(Listing).filter(Listing.id == open_house.listing_id).first()
        listing_agent = db.query(Agent).filter(Agent.id == listing.listing_agent_id).first()
        
        if not listing_agent or not listing_agent.email:
            return {"success": False, "error": "Listing agent email not found"}
        
        # Prepare template data
        template_data = {
            "listing_agent_name": listing_agent.name,
            "property_address": listing.address,
            "open_house_date": open_house.start_time.strftime("%A, %B %d, %Y"),
            "open_house_time": f"{open_house.start_time.strftime('%I:%M %p')} - {open_house.end_time.strftime('%I:%M %p')}",
            "recommended_agents": recommended_agents[:3],  # Top 3
            "open_house_id": open_house.id
        }
        
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .header { background-color: #2c3e50; color: white; padding: 20px; text-align: center; }
                .content { padding: 20px; }
                .agent-card { border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }
                .agent-score { background-color: #3498db; color: white; padding: 5px 10px; border-radius: 3px; display: inline-block; }
                .reasoning { font-style: italic; color: #666; margin-top: 10px; }
                .footer { background-color: #ecf0f1; padding: 15px; text-align: center; }
            </style>
        </head>
        <body>
            <div class="header">
                <h2>🏠 New Open House Agent Recommendations</h2>
            </div>
            <div class="content">
                <p>Hi {{ listing_agent_name }},</p>
                
                <p>We've identified the top agents to host your open house:</p>
                
                <h3>Property Details:</h3>
                <ul>
                    <li><strong>Address:</strong> {{ property_address }}</li>
                    <li><strong>Date:</strong> {{ open_house_date }}</li>
                    <li><strong>Time:</strong> {{ open_house_time }}</li>
                </ul>
                
                <h3>Recommended Agents:</h3>
                
                {% for agent in recommended_agents %}
                <div class="agent-card">
                    <h4>{{ agent.agent_name }} <span class="agent-score">Score: {{ "%.0f"|format(agent.score * 100) }}%</span></h4>
                    <p><strong>Why this agent:</strong></p>
                    <ul>
                        {% for factor in agent.reasoning.key_factors %}
                        <li>{{ factor }}</li>
                        {% endfor %}
                    </ul>
                    <div class="reasoning">
                        Experience: {{ agent.reasoning.experience_years }} years | 
                        Conversion Rate: {{ "%.1f"|format(agent.reasoning.conversion_rate * 100) }}% |
                        Area Familiar: {{ "Yes" if agent.reasoning.area_familiarity else "No" }}
                    </div>
                </div>
                {% endfor %}
                
                <p>To select an agent or view more details, please log into your dashboard.</p>
                
                <p>Best regards,<br>
                Open House Matchmaker AI</p>
            </div>
            <div class="footer">
                <p>This is an automated recommendation. Please review agent details before making your selection.</p>
            </div>
        </body>
        </html>
        """
        
        template = Template(html_template)
        html_content = template.render(**template_data)
        
        subject = f"Open House Agent Recommendations - {listing.address}"
        
        return self.send_email(listing_agent.email, subject, html_content)
    
    def send_agent_selection_notification(self, open_house: OpenHouse, 
                                        selected_agent: Agent, db: Session) -> Dict[str, Any]:
        """Notify agent they've been selected to host an open house"""
        listing = db.query(Listing).filter(Listing.id == open_house.listing_id).first()
        
        template_data = {
            "agent_name": selected_agent.name,
            "property_address": listing.address,
            "open_house_date": open_house.start_time.strftime("%A, %B %d, %Y"),
            "open_house_time": f"{open_house.start_time.strftime('%I:%M %p')} - {open_house.end_time.strftime('%I:%M %p')}",
            "property_details": {
                "price": f"${listing.price:,.0f}",
                "bedrooms": listing.bedrooms,
                "bathrooms": listing.bathrooms,
                "square_feet": listing.square_feet
            }
        }
        
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .header { background-color: #27ae60; color: white; padding: 20px; text-align: center; }
                .content { padding: 20px; }
                .property-details { background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0; }
                .footer { background-color: #ecf0f1; padding: 15px; text-align: center; }
            </style>
        </head>
        <body>
            <div class="header">
                <h2>🎉 You've Been Selected to Host an Open House!</h2>
            </div>
            <div class="content">
                <p>Hi {{ agent_name }},</p>
                
                <p>Great news! You've been selected to host an open house. Here are the details:</p>
                
                <div class="property-details">
                    <h3>Property Information:</h3>
                    <ul>
                        <li><strong>Address:</strong> {{ property_address }}</li>
                        <li><strong>Price:</strong> {{ property_details.price }}</li>
                        <li><strong>Bedrooms:</strong> {{ property_details.bedrooms }}</li>
                        <li><strong>Bathrooms:</strong> {{ property_details.bathrooms }}</li>
                        <li><strong>Square Feet:</strong> {{ property_details.square_feet }}</li>
                    </ul>
                    
                    <h3>Open House Details:</h3>
                    <ul>
                        <li><strong>Date:</strong> {{ open_house_date }}</li>
                        <li><strong>Time:</strong> {{ open_house_time }}</li>
                    </ul>
                </div>
                
                <p>Please confirm your availability and check your calendar for a meeting invite.</p>
                
                <p>Good luck with the open house!</p>
                
                <p>Best regards,<br>
                Open House Matchmaker Team</p>
            </div>
            <div class="footer">
                <p>If you have any questions, please contact your listing agent or the brokerage team.</p>
            </div>
        </body>
        </html>
        """
        
        template = Template(html_template)
        html_content = template.render(**template_data)
        
        subject = f"Open House Assignment - {listing.address}"
        
        return self.send_email(selected_agent.email, subject, html_content)
    
    def send_weekly_summary_email(self, recipients: List[str], 
                                 weekly_data: WeeklyRecommendations, db: Session) -> Dict[str, Any]:
        """Send weekly summary email to team"""
        template_data = {
            "week_start": weekly_data.week_start.strftime("%B %d, %Y"),
            "week_end": weekly_data.week_end.strftime("%B %d, %Y"),
            "total_open_houses": len(weekly_data.open_houses),
            "assigned_houses": len([oh for oh in weekly_data.open_houses if oh.host_agent_id]),
            "pending_assignments": len([oh for oh in weekly_data.open_houses if not oh.host_agent_id]),
            "summary_stats": weekly_data.summary_stats,
            "open_houses": weekly_data.open_houses[:10]  # Limit to first 10
        }
        
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .header { background-color: #34495e; color: white; padding: 20px; text-align: center; }
                .content { padding: 20px; }
                .stats { display: flex; justify-content: space-around; margin: 20px 0; }
                .stat-card { text-align: center; padding: 15px; background-color: #f8f9fa; border-radius: 5px; min-width: 150px; }
                .stat-number { font-size: 2em; font-weight: bold; color: #3498db; }
                .open-house-item { border-left: 4px solid #3498db; padding: 10px; margin: 10px 0; background-color: #f8f9fa; }
                .footer { background-color: #ecf0f1; padding: 15px; text-align: center; }
            </style>
        </head>
        <body>
            <div class="header">
                <h2>📊 Weekly Open House Summary</h2>
                <p>{{ week_start }} - {{ week_end }}</p>
            </div>
            <div class="content">
                <div class="stats">
                    <div class="stat-card">
                        <div class="stat-number">{{ total_open_houses }}</div>
                        <div>Total Open Houses</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{{ assigned_houses }}</div>
                        <div>Assigned</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{{ pending_assignments }}</div>
                        <div>Pending Assignment</div>
                    </div>
                    {% if summary_stats.avg_ml_score %}
                    <div class="stat-card">
                        <div class="stat-number">{{ "%.0f"|format(summary_stats.avg_ml_score * 100) }}%</div>
                        <div>Avg ML Score</div>
                    </div>
                    {% endif %}
                </div>
                
                <h3>Upcoming Open Houses:</h3>
                
                {% for open_house in open_houses %}
                <div class="open-house-item">
                    <h4>{{ open_house.listing.address }}</h4>
                    <p><strong>Date:</strong> {{ open_house.start_time.strftime("%A, %B %d") }} at {{ open_house.start_time.strftime("%I:%M %p") }}</p>
                    {% if open_house.host_agent %}
                    <p><strong>Host:</strong> {{ open_house.host_agent.name }}</p>
                    {% else %}
                    <p><strong>Status:</strong> <span style="color: #e74c3c;">Needs Assignment</span></p>
                    {% if open_house.agent_recommendations %}
                    <p><strong>Top Recommendation:</strong> {{ open_house.agent_recommendations[0].agent.name }} ({{ "%.0f"|format(open_house.agent_recommendations[0].score * 100) }}% match)</p>
                    {% endif %}
                    {% endif %}
                </div>
                {% endfor %}
                
                {% if total_open_houses > 10 %}
                <p><em>... and {{ total_open_houses - 10 }} more open houses this week.</em></p>
                {% endif %}
                
                <p>This summary was generated automatically by the Open House Matchmaker AI system.</p>
            </div>
            <div class="footer">
                <p>For detailed information, please log into your dashboard.</p>
            </div>
        </body>
        </html>
        """
        
        template = Template(html_template)
        html_content = template.render(**template_data)
        
        subject = f"Weekly Open House Summary - {weekly_data.week_start.strftime('%B %d')} to {weekly_data.week_end.strftime('%B %d')}"
        
        results = []
        for recipient in recipients:
            result = self.send_email(recipient, subject, html_content)
            results.append({"recipient": recipient, "result": result})
        
        return {
            "success": all(r["result"]["success"] for r in results),
            "results": results,
            "sent_count": sum(1 for r in results if r["result"]["success"])
        }
    
    def send_feedback_request_email(self, open_house: OpenHouse, db: Session) -> Dict[str, Any]:
        """Send feedback request after open house completion"""
        listing = db.query(Listing).filter(Listing.id == open_house.listing_id).first()
        listing_agent = db.query(Agent).filter(Agent.id == listing.listing_agent_id).first()
        host_agent = db.query(Agent).filter(Agent.id == open_house.host_agent_id).first()
        
        if not listing_agent or not listing_agent.email:
            return {"success": False, "error": "Listing agent email not found"}
        
        template_data = {
            "listing_agent_name": listing_agent.name,
            "host_agent_name": host_agent.name if host_agent else "Unknown",
            "property_address": listing.address,
            "open_house_date": open_house.start_time.strftime("%A, %B %d, %Y"),
            "attendee_count": open_house.attendee_count,
            "leads_generated": open_house.leads_generated,
            "open_house_id": open_house.id
        }
        
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .header { background-color: #9b59b6; color: white; padding: 20px; text-align: center; }
                .content { padding: 20px; }
                .results { background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0; }
                .button { background-color: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 10px 0; }
                .footer { background-color: #ecf0f1; padding: 15px; text-align: center; }
            </style>
        </head>
        <body>
            <div class="header">
                <h2>📝 Open House Feedback Request</h2>
            </div>
            <div class="content">
                <p>Hi {{ listing_agent_name }},</p>
                
                <p>Your open house has been completed! Here's a quick summary:</p>
                
                <div class="results">
                    <h3>Open House Results:</h3>
                    <ul>
                        <li><strong>Property:</strong> {{ property_address }}</li>
                        <li><strong>Date:</strong> {{ open_house_date }}</li>
                        <li><strong>Host Agent:</strong> {{ host_agent_name }}</li>
                        <li><strong>Attendees:</strong> {{ attendee_count }}</li>
                        <li><strong>Leads Generated:</strong> {{ leads_generated }}</li>
                    </ul>
                </div>
                
                <p>To help us improve our agent matching system, please provide feedback on the hosting agent's performance:</p>
                
                <a href="#" class="button">Provide Feedback</a>
                
                <p>Your feedback helps our AI system learn and provide better agent recommendations in the future.</p>
                
                <p>Thank you for using Open House Matchmaker!</p>
                
                <p>Best regards,<br>
                Open House Matchmaker Team</p>
            </div>
            <div class="footer">
                <p>This feedback is confidential and used only to improve our matching algorithm.</p>
            </div>
        </body>
        </html>
        """
        
        template = Template(html_template)
        html_content = template.render(**template_data)
        
        subject = f"Feedback Request - Open House at {listing.address}"
        
        return self.send_email(listing_agent.email, subject, html_content)

# Global instance
email_service = EmailService()
