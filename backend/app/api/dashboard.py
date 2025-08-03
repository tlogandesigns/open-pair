from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime, timedelta
from app.database.connection import get_db
from app.models.database_models import (
    Agent as DBAgent, 
    OpenHouse as DBOpenHouse, 
    Listing as DBListing,
    AgentPerformance as DBPerformance,
    AgentRecommendation as DBRecommendation
)
from app.models.schemas import DashboardStats, WeeklyRecommendations
from app.services.fairness_service import fairness_service
from app.ml.agent_scorer import agent_scorer
from app.integrations.email_service import email_service

router = APIRouter()

@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get dashboard statistics"""
    
    # Basic counts
    total_agents = db.query(DBAgent).count()
    active_agents = db.query(DBAgent).filter(DBAgent.is_active == True).count()
    
    # Open house counts
    now = datetime.utcnow()
    upcoming_open_houses = db.query(DBOpenHouse).filter(
        DBOpenHouse.start_time > now,
        DBOpenHouse.status == "Scheduled"
    ).count()
    
    # This month's completed open houses
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    completed_this_month = db.query(DBOpenHouse).filter(
        DBOpenHouse.start_time >= month_start,
        DBOpenHouse.status == "Completed"
    ).count()
    
    # Average conversion rate
    recent_performances = db.query(DBPerformance).filter(
        DBPerformance.period_start >= now - timedelta(days=90)
    ).all()
    
    if recent_performances:
        avg_conversion = sum(p.conversion_rate for p in recent_performances) / len(recent_performances)
    else:
        avg_conversion = 0.0
    
    # Top performing agents (last 30 days)
    thirty_days_ago = now - timedelta(days=30)
    top_agents_query = db.query(
        DBAgent.id,
        DBAgent.name,
        db.func.count(DBOpenHouse.id).label('open_houses_hosted'),
        db.func.sum(DBOpenHouse.leads_generated).label('total_leads'),
        db.func.avg(DBOpenHouse.attendee_count).label('avg_attendees')
    ).join(
        DBOpenHouse, DBOpenHouse.host_agent_id == DBAgent.id
    ).filter(
        DBOpenHouse.start_time >= thirty_days_ago,
        DBOpenHouse.status == "Completed"
    ).group_by(
        DBAgent.id, DBAgent.name
    ).order_by(
        db.func.sum(DBOpenHouse.leads_generated).desc()
    ).limit(5).all()
    
    top_performing_agents = []
    for agent_data in top_agents_query:
        top_performing_agents.append({
            "agent_id": agent_data.id,
            "agent_name": agent_data.name,
            "open_houses_hosted": agent_data.open_houses_hosted,
            "total_leads": agent_data.total_leads or 0,
            "avg_attendees": float(agent_data.avg_attendees) if agent_data.avg_attendees else 0.0
        })
    
    return DashboardStats(
        total_agents=total_agents,
        active_agents=active_agents,
        upcoming_open_houses=upcoming_open_houses,
        completed_open_houses_this_month=completed_this_month,
        average_conversion_rate=avg_conversion,
        top_performing_agents=top_performing_agents
    )

@router.get("/weekly-summary", response_model=WeeklyRecommendations)
async def get_weekly_summary(db: Session = Depends(get_db)):
    """Get weekly open house summary with recommendations"""
    
    # Get current week
    now = datetime.utcnow()
    week_start = now - timedelta(days=now.weekday())  # Monday
    week_end = week_start + timedelta(days=6)  # Sunday
    
    # Get open houses for the week
    open_houses = db.query(DBOpenHouse).filter(
        DBOpenHouse.start_time >= week_start,
        DBOpenHouse.start_time <= week_end
    ).order_by(DBOpenHouse.start_time).all()
    
    # Prepare open houses with recommendations
    open_houses_with_recs = []
    for oh in open_houses:
        recommendations = db.query(DBRecommendation).filter(
            DBRecommendation.open_house_id == oh.id
        ).order_by(DBRecommendation.rank).all()
        
        open_houses_with_recs.append({
            **oh.__dict__,
            "listing": oh.listing,
            "host_agent": oh.host_agent,
            "agent_recommendations": recommendations
        })
    
    # Calculate summary stats
    total_houses = len(open_houses)
    assigned_houses = len([oh for oh in open_houses if oh.host_agent_id])
    pending_houses = total_houses - assigned_houses
    
    # Average ML scores
    all_recommendations = db.query(DBRecommendation).join(DBOpenHouse).filter(
        DBOpenHouse.start_time >= week_start,
        DBOpenHouse.start_time <= week_end
    ).all()
    
    avg_ml_score = 0.0
    if all_recommendations:
        avg_ml_score = sum(r.score for r in all_recommendations) / len(all_recommendations)
    
    summary_stats = {
        "total_open_houses": total_houses,
        "assigned_houses": assigned_houses,
        "pending_houses": pending_houses,
        "avg_ml_score": avg_ml_score,
        "recommendations_generated": len(all_recommendations)
    }
    
    return WeeklyRecommendations(
        week_start=week_start,
        week_end=week_end,
        open_houses=open_houses_with_recs,
        summary_stats=summary_stats
    )

@router.post("/send-weekly-email")
async def send_weekly_email(
    recipients: List[str],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Send weekly summary email to specified recipients"""
    
    # Get weekly data
    weekly_data = await get_weekly_summary(db)
    
    # Send email in background
    background_tasks.add_task(
        send_weekly_email_task,
        recipients,
        weekly_data,
        db
    )
    
    return {"message": f"Weekly summary email scheduled for {len(recipients)} recipients"}

@router.get("/fairness-report")
async def get_fairness_report(db: Session = Depends(get_db)):
    """Get fairness report for all agents"""
    return fairness_service.get_fairness_report(datetime.utcnow(), db)

@router.post("/retrain-model")
async def retrain_model(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Retrain the agent scoring model"""
    
    background_tasks.add_task(retrain_model_task, db)
    
    return {"message": "Model retraining started in background"}

@router.get("/model-performance")
async def get_model_performance(db: Session = Depends(get_db)):
    """Get current model performance metrics"""
    
    # Get recent predictions vs outcomes
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    recent_recommendations = db.query(DBRecommendation).join(DBOpenHouse).filter(
        DBOpenHouse.start_time >= thirty_days_ago,
        DBOpenHouse.status == "Completed",
        DBRecommendation.was_selected == True
    ).all()
    
    if not recent_recommendations:
        return {
            "message": "Insufficient data for performance evaluation",
            "total_predictions": 0
        }
    
    # Calculate accuracy metrics
    total_predictions = len(recent_recommendations)
    high_score_successes = 0
    low_score_failures = 0
    
    for rec in recent_recommendations:
        open_house = rec.open_house
        if not open_house:
            continue
        
        # Define success as having leads generated
        was_successful = open_house.leads_generated > 0
        had_high_score = rec.score > 0.7
        
        if had_high_score and was_successful:
            high_score_successes += 1
        elif not had_high_score and not was_successful:
            low_score_failures += 1
    
    accuracy = (high_score_successes + low_score_failures) / total_predictions if total_predictions > 0 else 0
    
    # Get average scores by rank
    rank_performance = {}
    for rank in [1, 2, 3]:
        rank_recs = [r for r in recent_recommendations if r.rank == rank]
        if rank_recs:
            avg_score = sum(r.score for r in rank_recs) / len(rank_recs)
            success_rate = sum(1 for r in rank_recs if r.open_house and r.open_house.leads_generated > 0) / len(rank_recs)
            rank_performance[f"rank_{rank}"] = {
                "avg_score": avg_score,
                "success_rate": success_rate,
                "count": len(rank_recs)
            }
    
    return {
        "model_version": agent_scorer.model_version,
        "evaluation_period_days": 30,
        "total_predictions": total_predictions,
        "accuracy": accuracy,
        "rank_performance": rank_performance,
        "high_score_threshold": 0.7
    }

@router.get("/upcoming-unassigned")
async def get_upcoming_unassigned(days_ahead: int = 7, db: Session = Depends(get_db)):
    """Get upcoming open houses that need agent assignment"""
    
    start_date = datetime.utcnow()
    end_date = start_date + timedelta(days=days_ahead)
    
    unassigned = db.query(DBOpenHouse).filter(
        DBOpenHouse.start_time >= start_date,
        DBOpenHouse.start_time <= end_date,
        DBOpenHouse.host_agent_id.is_(None),
        DBOpenHouse.status == "Scheduled"
    ).order_by(DBOpenHouse.start_time).all()
    
    result = []
    for oh in unassigned:
        recommendations = db.query(DBRecommendation).filter(
            DBRecommendation.open_house_id == oh.id
        ).order_by(DBRecommendation.rank).limit(3).all()
        
        result.append({
            "open_house": oh,
            "listing": oh.listing,
            "days_until": (oh.start_time - start_date).days,
            "hours_until": (oh.start_time - start_date).total_seconds() / 3600,
            "top_recommendations": recommendations
        })
    
    return {
        "count": len(result),
        "unassigned_open_houses": result
    }

# Background task functions
async def send_weekly_email_task(recipients: List[str], weekly_data: WeeklyRecommendations, db: Session):
    """Background task to send weekly email"""
    try:
        from app.database.connection import SessionLocal
        task_db = SessionLocal()
        
        email_service.send_weekly_summary_email(recipients, weekly_data, task_db)
        
        task_db.close()
        
    except Exception as e:
        print(f"Error sending weekly email: {e}")

async def retrain_model_task(db: Session):
    """Background task to retrain the ML model"""
    try:
        from app.database.connection import SessionLocal
        task_db = SessionLocal()
        
        training_result = agent_scorer.train_model(task_db)
        print(f"Model retraining completed: {training_result}")
        
        task_db.close()
        
    except Exception as e:
        print(f"Error retraining model: {e}")
