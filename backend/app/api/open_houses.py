from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from app.database.connection import get_db
from app.models.database_models import (
    OpenHouse as DBOpenHouse, 
    Listing as DBListing, 
    Agent as DBAgent,
    AgentRecommendation as DBAgentRecommendation,
    FeedbackScore as DBFeedbackScore
)
from app.models.schemas import (
    OpenHouse, OpenHouseCreate, OpenHouseUpdate, OpenHouseWithRecommendations,
    AgentMatchingResponse, FeedbackScoreCreate, FeedbackScore
)
from app.ml.agent_scorer import agent_scorer
from app.services.fairness_service import fairness_service
from app.integrations.calendar_service import calendar_service
from app.integrations.email_service import email_service

router = APIRouter()

@router.get("/", response_model=List[OpenHouse])
async def get_open_houses(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    agent_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get open houses with optional filters"""
    query = db.query(DBOpenHouse)
    
    if status:
        query = query.filter(DBOpenHouse.status == status)
    if start_date:
        query = query.filter(DBOpenHouse.start_time >= start_date)
    if end_date:
        query = query.filter(DBOpenHouse.start_time <= end_date)
    if agent_id:
        query = query.filter(DBOpenHouse.host_agent_id == agent_id)
    
    open_houses = query.order_by(DBOpenHouse.start_time.asc()).offset(skip).limit(limit).all()
    return open_houses

@router.get("/{open_house_id}", response_model=OpenHouseWithRecommendations)
async def get_open_house(open_house_id: int, db: Session = Depends(get_db)):
    """Get open house with recommendations"""
    open_house = db.query(DBOpenHouse).filter(DBOpenHouse.id == open_house_id).first()
    if not open_house:
        raise HTTPException(status_code=404, detail="Open house not found")
    
    # Get recommendations
    recommendations = db.query(DBAgentRecommendation).filter(
        DBAgentRecommendation.open_house_id == open_house_id
    ).order_by(DBAgentRecommendation.rank).all()
    
    return {
        **open_house.__dict__,
        "listing": open_house.listing,
        "host_agent": open_house.host_agent,
        "agent_recommendations": recommendations
    }

@router.post("/", response_model=OpenHouse)
async def create_open_house(
    open_house_data: OpenHouseCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create new open house and generate agent recommendations"""
    # Verify listing exists
    listing = db.query(DBListing).filter(DBListing.id == open_house_data.listing_id).first()
    if not listing:
        raise HTTPException(status_code=400, detail="Listing not found")
    
    # Create open house
    db_open_house = DBOpenHouse(**open_house_data.dict())
    db.add(db_open_house)
    db.commit()
    db.refresh(db_open_house)
    
    # Generate agent recommendations in background
    background_tasks.add_task(
        generate_agent_recommendations,
        db_open_house.id,
        db
    )
    
    return db_open_house

@router.put("/{open_house_id}", response_model=OpenHouse)
async def update_open_house(
    open_house_id: int,
    open_house_update: OpenHouseUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Update open house information"""
    open_house = db.query(DBOpenHouse).filter(DBOpenHouse.id == open_house_id).first()
    if not open_house:
        raise HTTPException(status_code=404, detail="Open house not found")
    
    update_data = open_house_update.dict(exclude_unset=True)
    
    # If host agent is being assigned, send notifications
    if "host_agent_id" in update_data and update_data["host_agent_id"]:
        old_agent_id = open_house.host_agent_id
        new_agent_id = update_data["host_agent_id"]
        
        if old_agent_id != new_agent_id:
            # Update the recommendation as selected
            recommendation = db.query(DBAgentRecommendation).filter(
                DBAgentRecommendation.open_house_id == open_house_id,
                DBAgentRecommendation.agent_id == new_agent_id
            ).first()
            
            if recommendation:
                recommendation.was_selected = True
                db.commit()
            
            # Send notifications in background
            background_tasks.add_task(
                send_agent_selection_notifications,
                open_house_id,
                new_agent_id,
                db
            )
    
    # Apply updates
    for field, value in update_data.items():
        setattr(open_house, field, value)
    
    db.commit()
    db.refresh(open_house)
    return open_house

@router.delete("/{open_house_id}")
async def cancel_open_house(open_house_id: int, db: Session = Depends(get_db)):
    """Cancel open house"""
    open_house = db.query(DBOpenHouse).filter(DBOpenHouse.id == open_house_id).first()
    if not open_house:
        raise HTTPException(status_code=404, detail="Open house not found")
    
    open_house.status = "Cancelled"
    db.commit()
    return {"message": "Open house cancelled successfully"}

@router.post("/{open_house_id}/generate-recommendations", response_model=AgentMatchingResponse)
async def generate_recommendations(open_house_id: int, db: Session = Depends(get_db)):
    """Generate or regenerate agent recommendations for an open house"""
    open_house = db.query(DBOpenHouse).filter(DBOpenHouse.id == open_house_id).first()
    if not open_house:
        raise HTTPException(status_code=404, detail="Open house not found")
    
    if not open_house.listing:
        raise HTTPException(status_code=400, detail="Listing not found for open house")
    
    # Get available agents
    agents = db.query(DBAgent).filter(DBAgent.is_active == True).all()
    
    # Score agents using ML model
    agent_scores = agent_scorer.score_agents(
        agents, open_house.listing, open_house.start_time, db
    )
    
    # Apply fairness adjustments
    fair_scores = fairness_service.apply_fairness_adjustments(
        agent_scores, open_house.start_time, db
    )
    
    # Ensure diversity in top 3
    final_recommendations = fairness_service.ensure_diversity_in_recommendations(
        fair_scores, db
    )
    
    # Clear existing recommendations
    db.query(DBAgentRecommendation).filter(
        DBAgentRecommendation.open_house_id == open_house_id
    ).delete()
    
    # Save new recommendations
    for rank, score_detail in enumerate(final_recommendations[:3], 1):
        recommendation = DBAgentRecommendation(
            open_house_id=open_house_id,
            agent_id=score_detail.agent_id,
            score=score_detail.score,
            rank=rank,
            reasoning=score_detail.reasoning
        )
        db.add(recommendation)
    
    db.commit()
    
    return AgentMatchingResponse(
        open_house_id=open_house_id,
        recommendations=final_recommendations[:3],
        model_version=agent_scorer.model_version,
        generated_at=datetime.utcnow()
    )

@router.post("/{open_house_id}/feedback", response_model=FeedbackScore)
async def submit_feedback(
    open_house_id: int,
    feedback_data: FeedbackScoreCreate,
    db: Session = Depends(get_db)
):
    """Submit feedback for completed open house"""
    open_house = db.query(DBOpenHouse).filter(DBOpenHouse.id == open_house_id).first()
    if not open_house:
        raise HTTPException(status_code=404, detail="Open house not found")
    
    if open_house.status != "Completed":
        raise HTTPException(status_code=400, detail="Can only provide feedback for completed open houses")
    
    db_feedback = DBFeedbackScore(
        open_house_id=open_house_id,
        **feedback_data.dict()
    )
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)
    
    return db_feedback

@router.get("/{open_house_id}/feedback", response_model=List[FeedbackScore])
async def get_feedback(open_house_id: int, db: Session = Depends(get_db)):
    """Get all feedback for an open house"""
    feedback = db.query(DBFeedbackScore).filter(
        DBFeedbackScore.open_house_id == open_house_id
    ).all()
    return feedback

@router.post("/{open_house_id}/complete")
async def complete_open_house(
    open_house_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Mark open house as completed and trigger feedback request"""
    open_house = db.query(DBOpenHouse).filter(DBOpenHouse.id == open_house_id).first()
    if not open_house:
        raise HTTPException(status_code=404, detail="Open house not found")
    
    open_house.status = "Completed"
    db.commit()
    
    # Send feedback request in background
    background_tasks.add_task(
        send_feedback_request,
        open_house_id,
        db
    )
    
    return {"message": "Open house marked as completed"}

@router.get("/upcoming/week", response_model=List[OpenHouseWithRecommendations])
async def get_upcoming_week(db: Session = Depends(get_db)):
    """Get upcoming open houses for the next 7 days"""
    start_date = datetime.utcnow()
    end_date = start_date + timedelta(days=7)
    
    open_houses = db.query(DBOpenHouse).filter(
        DBOpenHouse.start_time >= start_date,
        DBOpenHouse.start_time <= end_date,
        DBOpenHouse.status == "Scheduled"
    ).order_by(DBOpenHouse.start_time).all()
    
    result = []
    for oh in open_houses:
        recommendations = db.query(DBAgentRecommendation).filter(
            DBAgentRecommendation.open_house_id == oh.id
        ).order_by(DBAgentRecommendation.rank).all()
        
        result.append({
            **oh.__dict__,
            "listing": oh.listing,
            "host_agent": oh.host_agent,
            "agent_recommendations": recommendations
        })
    
    return result

# Background task functions
async def generate_agent_recommendations(open_house_id: int, db: Session):
    """Background task to generate agent recommendations"""
    try:
        # Re-create database session for background task
        from app.database.connection import SessionLocal
        task_db = SessionLocal()
        
        open_house = task_db.query(DBOpenHouse).filter(DBOpenHouse.id == open_house_id).first()
        if not open_house or not open_house.listing:
            return
        
        # Get available agents
        agents = task_db.query(DBAgent).filter(DBAgent.is_active == True).all()
        
        # Score agents
        agent_scores = agent_scorer.score_agents(
            agents, open_house.listing, open_house.start_time, task_db
        )
        
        # Apply fairness adjustments
        fair_scores = fairness_service.apply_fairness_adjustments(
            agent_scores, open_house.start_time, task_db
        )
        
        # Get top 3 recommendations
        final_recommendations = fairness_service.ensure_diversity_in_recommendations(
            fair_scores, task_db
        )
        
        # Save recommendations
        for rank, score_detail in enumerate(final_recommendations[:3], 1):
            recommendation = DBAgentRecommendation(
                open_house_id=open_house_id,
                agent_id=score_detail.agent_id,
                score=score_detail.score,
                rank=rank,
                reasoning=score_detail.reasoning
            )
            task_db.add(recommendation)
        
        task_db.commit()
        
        # Send notification email to listing agent
        email_service.send_agent_recommendation_notification(
            open_house, final_recommendations, task_db
        )
        
        task_db.close()
        
    except Exception as e:
        print(f"Error generating recommendations: {e}")

async def send_agent_selection_notifications(open_house_id: int, agent_id: int, db: Session):
    """Background task to send agent selection notifications"""
    try:
        from app.database.connection import SessionLocal
        task_db = SessionLocal()
        
        open_house = task_db.query(DBOpenHouse).filter(DBOpenHouse.id == open_house_id).first()
        agent = task_db.query(DBAgent).filter(DBAgent.id == agent_id).first()
        
        if open_house and agent and open_house.listing:
            # Send email notification
            email_service.send_agent_selection_notification(open_house, agent, task_db)
            
            # Create calendar invite
            calendar_service.create_calendar_invite(
                open_house, agent, open_house.listing.address
            )
        
        task_db.close()
        
    except Exception as e:
        print(f"Error sending selection notifications: {e}")

async def send_feedback_request(open_house_id: int, db: Session):
    """Background task to send feedback request"""
    try:
        from app.database.connection import SessionLocal
        task_db = SessionLocal()
        
        open_house = task_db.query(DBOpenHouse).filter(DBOpenHouse.id == open_house_id).first()
        if open_house:
            email_service.send_feedback_request_email(open_house, task_db)
        
        task_db.close()
        
    except Exception as e:
        print(f"Error sending feedback request: {e}")
