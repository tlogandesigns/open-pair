from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base

class Agent(Base):
    __tablename__ = "agents"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phone = Column(String)
    license_number = Column(String, unique=True)
    experience_years = Column(Integer, default=0)
    areas_of_expertise = Column(JSON)  # List of zip codes or neighborhoods
    buyer_price_ranges = Column(JSON)  # Historical buyer price ranges
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    open_houses = relationship("OpenHouse", back_populates="host_agent")
    performance_metrics = relationship("AgentPerformance", back_populates="agent")
    availability = relationship("AgentAvailability", back_populates="agent")

class Listing(Base):
    __tablename__ = "listings"
    
    id = Column(Integer, primary_key=True, index=True)
    mls_number = Column(String, unique=True, nullable=False)
    address = Column(String, nullable=False)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    zip_code = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    bedrooms = Column(Integer)
    bathrooms = Column(Float)
    square_feet = Column(Integer)
    property_type = Column(String)  # Single Family, Condo, Townhouse, etc.
    listing_agent_id = Column(Integer, ForeignKey("agents.id"))
    listing_date = Column(DateTime(timezone=True))
    status = Column(String, default="Active")  # Active, Pending, Sold, Expired
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    listing_agent = relationship("Agent")
    open_houses = relationship("OpenHouse", back_populates="listing")

class OpenHouse(Base):
    __tablename__ = "open_houses"
    
    id = Column(Integer, primary_key=True, index=True)
    listing_id = Column(Integer, ForeignKey("listings.id"), nullable=False)
    host_agent_id = Column(Integer, ForeignKey("agents.id"))
    scheduled_date = Column(DateTime(timezone=True), nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    status = Column(String, default="Scheduled")  # Scheduled, Completed, Cancelled
    attendee_count = Column(Integer, default=0)
    leads_generated = Column(Integer, default=0)
    follow_ups_scheduled = Column(Integer, default=0)
    offers_received = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    notes = Column(Text)
    
    # Relationships
    listing = relationship("Listing", back_populates="open_houses")
    host_agent = relationship("Agent", back_populates="open_houses")
    agent_recommendations = relationship("AgentRecommendation", back_populates="open_house")

class AgentRecommendation(Base):
    __tablename__ = "agent_recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    open_house_id = Column(Integer, ForeignKey("open_houses.id"), nullable=False)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    score = Column(Float, nullable=False)  # AI confidence score (0-1)
    rank = Column(Integer, nullable=False)  # 1, 2, 3 for top recommendations
    reasoning = Column(JSON)  # Explanation of why this agent was recommended
    was_selected = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    open_house = relationship("OpenHouse", back_populates="agent_recommendations")
    agent = relationship("Agent")

class AgentPerformance(Base):
    __tablename__ = "agent_performance"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    open_house_id = Column(Integer, ForeignKey("open_houses.id"))
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    open_houses_hosted = Column(Integer, default=0)
    total_attendees = Column(Integer, default=0)
    total_leads = Column(Integer, default=0)
    total_follow_ups = Column(Integer, default=0)
    total_offers = Column(Integer, default=0)
    conversion_rate = Column(Float, default=0.0)  # leads / attendees
    success_rate = Column(Float, default=0.0)  # offers / leads
    average_feedback_score = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    agent = relationship("Agent", back_populates="performance_metrics")
    open_house = relationship("OpenHouse")

class AgentAvailability(Base):
    __tablename__ = "agent_availability"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    day_of_week = Column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time = Column(String, nullable=False)  # "09:00"
    end_time = Column(String, nullable=False)  # "17:00"
    is_recurring = Column(Boolean, default=True)
    specific_date = Column(DateTime(timezone=True))  # For one-time availability
    is_available = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    agent = relationship("Agent", back_populates="availability")

class FeedbackScore(Base):
    __tablename__ = "feedback_scores"
    
    id = Column(Integer, primary_key=True, index=True)
    open_house_id = Column(Integer, ForeignKey("open_houses.id"), nullable=False)
    feedback_from = Column(String, nullable=False)  # "listing_agent", "buyer", "visitor"
    score = Column(Integer, nullable=False)  # 1-5 rating
    comments = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    open_house = relationship("OpenHouse")
