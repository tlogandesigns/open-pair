from pydantic import BaseModel, EmailStr, validator
from typing import List, Optional, Dict, Any
from datetime import datetime, time
from enum import Enum

class PropertyType(str, Enum):
    SINGLE_FAMILY = "Single Family"
    CONDO = "Condo"
    TOWNHOUSE = "Townhouse"
    MULTI_FAMILY = "Multi Family"

class ListingStatus(str, Enum):
    ACTIVE = "Active"
    PENDING = "Pending"
    SOLD = "Sold"
    EXPIRED = "Expired"

class OpenHouseStatus(str, Enum):
    SCHEDULED = "Scheduled"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"

# Agent Models
class AgentBase(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    license_number: Optional[str] = None
    experience_years: int = 0
    areas_of_expertise: List[str] = []
    buyer_price_ranges: List[Dict[str, float]] = []

class AgentCreate(AgentBase):
    pass

class AgentUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    experience_years: Optional[int] = None
    areas_of_expertise: Optional[List[str]] = None
    buyer_price_ranges: Optional[List[Dict[str, float]]] = None
    is_active: Optional[bool] = None

class Agent(AgentBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Listing Models
class ListingBase(BaseModel):
    mls_number: str
    address: str
    city: str
    state: str
    zip_code: str
    price: float
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    square_feet: Optional[int] = None
    property_type: Optional[PropertyType] = None
    listing_agent_id: int
    listing_date: Optional[datetime] = None

class ListingCreate(ListingBase):
    pass

class ListingUpdate(BaseModel):
    price: Optional[float] = None
    status: Optional[ListingStatus] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    square_feet: Optional[int] = None

class Listing(ListingBase):
    id: int
    status: ListingStatus
    created_at: datetime

    class Config:
        from_attributes = True

# Open House Models
class OpenHouseBase(BaseModel):
    listing_id: int
    scheduled_date: datetime
    start_time: datetime
    end_time: datetime

class OpenHouseCreate(OpenHouseBase):
    pass

class OpenHouseUpdate(BaseModel):
    host_agent_id: Optional[int] = None
    status: Optional[OpenHouseStatus] = None
    attendee_count: Optional[int] = None
    leads_generated: Optional[int] = None
    follow_ups_scheduled: Optional[int] = None
    offers_received: Optional[int] = None
    notes: Optional[str] = None

class OpenHouse(OpenHouseBase):
    id: int
    host_agent_id: Optional[int] = None
    status: OpenHouseStatus
    attendee_count: int
    leads_generated: int
    follow_ups_scheduled: int
    offers_received: int
    created_at: datetime
    notes: Optional[str] = None

    class Config:
        from_attributes = True

# Agent Recommendation Models
class AgentRecommendationBase(BaseModel):
    agent_id: int
    score: float
    rank: int
    reasoning: Dict[str, Any]

class AgentRecommendation(AgentRecommendationBase):
    id: int
    open_house_id: int
    was_selected: bool
    created_at: datetime
    agent: Agent

    class Config:
        from_attributes = True

class OpenHouseWithRecommendations(OpenHouse):
    listing: Listing
    host_agent: Optional[Agent] = None
    agent_recommendations: List[AgentRecommendation] = []

# Agent Performance Models
class AgentPerformanceBase(BaseModel):
    period_start: datetime
    period_end: datetime
    open_houses_hosted: int = 0
    total_attendees: int = 0
    total_leads: int = 0
    total_follow_ups: int = 0
    total_offers: int = 0
    conversion_rate: float = 0.0
    success_rate: float = 0.0
    average_feedback_score: float = 0.0

class AgentPerformance(AgentPerformanceBase):
    id: int
    agent_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Agent Availability Models
class AgentAvailabilityBase(BaseModel):
    day_of_week: int
    start_time: str
    end_time: str
    is_recurring: bool = True
    specific_date: Optional[datetime] = None
    is_available: bool = True

    @validator('day_of_week')
    def validate_day_of_week(cls, v):
        if not 0 <= v <= 6:
            raise ValueError('day_of_week must be between 0 (Monday) and 6 (Sunday)')
        return v

class AgentAvailabilityCreate(AgentAvailabilityBase):
    pass

class AgentAvailability(AgentAvailabilityBase):
    id: int
    agent_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Feedback Models
class FeedbackScoreBase(BaseModel):
    feedback_from: str
    score: int
    comments: Optional[str] = None

    @validator('score')
    def validate_score(cls, v):
        if not 1 <= v <= 5:
            raise ValueError('score must be between 1 and 5')
        return v

class FeedbackScoreCreate(FeedbackScoreBase):
    pass

class FeedbackScore(FeedbackScoreBase):
    id: int
    open_house_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Dashboard Models
class DashboardStats(BaseModel):
    total_agents: int
    active_agents: int
    upcoming_open_houses: int
    completed_open_houses_this_month: int
    average_conversion_rate: float
    top_performing_agents: List[Dict[str, Any]]

class WeeklyRecommendations(BaseModel):
    week_start: datetime
    week_end: datetime
    open_houses: List[OpenHouseWithRecommendations]
    summary_stats: Dict[str, Any]

# ML Model Response
class AgentScoreDetails(BaseModel):
    agent_id: int
    agent_name: str
    score: float
    confidence: float
    reasoning: Dict[str, Any]
    availability_confirmed: bool

class AgentMatchingResponse(BaseModel):
    open_house_id: int
    recommendations: List[AgentScoreDetails]
    model_version: str
    generated_at: datetime
