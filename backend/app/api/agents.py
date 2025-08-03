from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.database.connection import get_db
from app.models.database_models import Agent as DBAgent, AgentAvailability as DBAvailability, AgentPerformance as DBPerformance
from app.models.schemas import Agent, AgentCreate, AgentUpdate, AgentAvailability, AgentAvailabilityCreate, AgentPerformance
from app.services.fairness_service import fairness_service

router = APIRouter()

@router.get("/", response_model=List[Agent])
async def get_agents(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """Get all agents"""
    query = db.query(DBAgent)
    if active_only:
        query = query.filter(DBAgent.is_active == True)
    
    agents = query.offset(skip).limit(limit).all()
    return agents

@router.get("/{agent_id}", response_model=Agent)
async def get_agent(agent_id: int, db: Session = Depends(get_db)):
    """Get agent by ID"""
    agent = db.query(DBAgent).filter(DBAgent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

@router.post("/", response_model=Agent)
async def create_agent(agent_data: AgentCreate, db: Session = Depends(get_db)):
    """Create new agent"""
    # Check if email already exists
    existing_agent = db.query(DBAgent).filter(DBAgent.email == agent_data.email).first()
    if existing_agent:
        raise HTTPException(status_code=400, detail="Agent with this email already exists")
    
    db_agent = DBAgent(**agent_data.dict())
    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)
    return db_agent

@router.put("/{agent_id}", response_model=Agent)
async def update_agent(
    agent_id: int,
    agent_update: AgentUpdate,
    db: Session = Depends(get_db)
):
    """Update agent information"""
    agent = db.query(DBAgent).filter(DBAgent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    update_data = agent_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(agent, field, value)
    
    agent.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(agent)
    return agent

@router.delete("/{agent_id}")
async def deactivate_agent(agent_id: int, db: Session = Depends(get_db)):
    """Deactivate agent (soft delete)"""
    agent = db.query(DBAgent).filter(DBAgent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent.is_active = False
    agent.updated_at = datetime.utcnow()
    db.commit()
    return {"message": "Agent deactivated successfully"}

@router.get("/{agent_id}/availability", response_model=List[AgentAvailability])
async def get_agent_availability(agent_id: int, db: Session = Depends(get_db)):
    """Get agent availability schedule"""
    agent = db.query(DBAgent).filter(DBAgent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    availability = db.query(DBAvailability).filter(
        DBAvailability.agent_id == agent_id
    ).all()
    return availability

@router.post("/{agent_id}/availability", response_model=AgentAvailability)
async def add_agent_availability(
    agent_id: int,
    availability_data: AgentAvailabilityCreate,
    db: Session = Depends(get_db)
):
    """Add agent availability"""
    agent = db.query(DBAgent).filter(DBAgent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    db_availability = DBAvailability(
        agent_id=agent_id,
        **availability_data.dict()
    )
    db.add(db_availability)
    db.commit()
    db.refresh(db_availability)
    return db_availability

@router.delete("/{agent_id}/availability/{availability_id}")
async def remove_agent_availability(
    agent_id: int,
    availability_id: int,
    db: Session = Depends(get_db)
):
    """Remove agent availability"""
    availability = db.query(DBAvailability).filter(
        DBAvailability.id == availability_id,
        DBAvailability.agent_id == agent_id
    ).first()
    
    if not availability:
        raise HTTPException(status_code=404, detail="Availability not found")
    
    db.delete(availability)
    db.commit()
    return {"message": "Availability removed successfully"}

@router.get("/{agent_id}/performance", response_model=List[AgentPerformance])
async def get_agent_performance(
    agent_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """Get agent performance metrics"""
    agent = db.query(DBAgent).filter(DBAgent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    query = db.query(DBPerformance).filter(DBPerformance.agent_id == agent_id)
    
    if start_date:
        query = query.filter(DBPerformance.period_start >= start_date)
    if end_date:
        query = query.filter(DBPerformance.period_end <= end_date)
    
    performance = query.order_by(DBPerformance.period_start.desc()).all()
    return performance

@router.get("/{agent_id}/fairness-score")
async def get_agent_fairness_score(agent_id: int, db: Session = Depends(get_db)):
    """Get agent's current fairness score"""
    agent = db.query(DBAgent).filter(DBAgent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    fairness_score = fairness_service.calculate_fairness_score(
        agent, datetime.utcnow(), db
    )
    
    opportunity_counts = fairness_service.get_opportunity_counts(
        agent_id, datetime.utcnow(), db
    )
    
    tier = fairness_service.get_agent_tier(agent)
    
    return {
        "agent_id": agent_id,
        "agent_name": agent.name,
        "fairness_score": fairness_score,
        "tier": tier,
        "opportunities_last_30_days": opportunity_counts["hosted_30_days"],
        "recommendations_last_30_days": opportunity_counts["recommended_30_days"],
        "minimum_monthly_opportunities": fairness_service.min_opportunities_per_month[tier],
        "maximum_monthly_opportunities": fairness_service.max_opportunities_per_month[tier]
    }

@router.get("/search/by-area")
async def search_agents_by_area(
    zip_code: str = None,
    city: str = None,
    db: Session = Depends(get_db)
):
    """Search agents by area expertise"""
    agents = db.query(DBAgent).filter(DBAgent.is_active == True).all()
    
    matching_agents = []
    for agent in agents:
        areas = agent.areas_of_expertise or []
        if zip_code and zip_code in areas:
            matching_agents.append(agent)
        elif city and any(city.lower() in area.lower() for area in areas):
            matching_agents.append(agent)
    
    return matching_agents

@router.get("/search/by-price-range")
async def search_agents_by_price_range(
    min_price: float,
    max_price: float,
    db: Session = Depends(get_db)
):
    """Search agents by buyer price range experience"""
    agents = db.query(DBAgent).filter(DBAgent.is_active == True).all()
    
    matching_agents = []
    for agent in agents:
        price_ranges = agent.buyer_price_ranges or []
        for price_range in price_ranges:
            if (price_range.get('min', 0) <= max_price and 
                price_range.get('max', float('inf')) >= min_price):
                matching_agents.append(agent)
                break
    
    return matching_agents
