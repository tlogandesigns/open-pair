from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.database.connection import get_db
from app.models.database_models import Listing as DBListing, Agent as DBAgent
from app.models.schemas import Listing, ListingCreate, ListingUpdate, ListingStatus

router = APIRouter()

@router.get("/", response_model=List[Listing])
async def get_listings(
    skip: int = 0,
    limit: int = 100,
    status: Optional[ListingStatus] = None,
    agent_id: Optional[int] = None,
    city: Optional[str] = None,
    zip_code: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """Get listings with optional filters"""
    query = db.query(DBListing)
    
    if status:
        query = query.filter(DBListing.status == status)
    if agent_id:
        query = query.filter(DBListing.listing_agent_id == agent_id)
    if city:
        query = query.filter(DBListing.city.ilike(f"%{city}%"))
    if zip_code:
        query = query.filter(DBListing.zip_code == zip_code)
    if min_price:
        query = query.filter(DBListing.price >= min_price)
    if max_price:
        query = query.filter(DBListing.price <= max_price)
    
    listings = query.order_by(DBListing.created_at.desc()).offset(skip).limit(limit).all()
    return listings

@router.get("/{listing_id}", response_model=Listing)
async def get_listing(listing_id: int, db: Session = Depends(get_db)):
    """Get listing by ID"""
    listing = db.query(DBListing).filter(DBListing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing

@router.post("/", response_model=Listing)
async def create_listing(listing_data: ListingCreate, db: Session = Depends(get_db)):
    """Create new listing"""
    # Verify listing agent exists
    agent = db.query(DBAgent).filter(DBAgent.id == listing_data.listing_agent_id).first()
    if not agent:
        raise HTTPException(status_code=400, detail="Listing agent not found")
    
    # Check if MLS number already exists
    existing_listing = db.query(DBListing).filter(
        DBListing.mls_number == listing_data.mls_number
    ).first()
    if existing_listing:
        raise HTTPException(status_code=400, detail="Listing with this MLS number already exists")
    
    db_listing = DBListing(**listing_data.dict())
    db.add(db_listing)
    db.commit()
    db.refresh(db_listing)
    return db_listing

@router.put("/{listing_id}", response_model=Listing)
async def update_listing(
    listing_id: int,
    listing_update: ListingUpdate,
    db: Session = Depends(get_db)
):
    """Update listing information"""
    listing = db.query(DBListing).filter(DBListing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    update_data = listing_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(listing, field, value)
    
    db.commit()
    db.refresh(listing)
    return listing

@router.delete("/{listing_id}")
async def delete_listing(listing_id: int, db: Session = Depends(get_db)):
    """Delete listing"""
    listing = db.query(DBListing).filter(DBListing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    db.delete(listing)
    db.commit()
    return {"message": "Listing deleted successfully"}

@router.get("/search/by-mls/{mls_number}", response_model=Listing)
async def get_listing_by_mls(mls_number: str, db: Session = Depends(get_db)):
    """Get listing by MLS number"""
    listing = db.query(DBListing).filter(DBListing.mls_number == mls_number).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing

@router.get("/agent/{agent_id}", response_model=List[Listing])
async def get_agent_listings(
    agent_id: int,
    status: Optional[ListingStatus] = None,
    db: Session = Depends(get_db)
):
    """Get all listings for a specific agent"""
    agent = db.query(DBAgent).filter(DBAgent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    query = db.query(DBListing).filter(DBListing.listing_agent_id == agent_id)
    if status:
        query = query.filter(DBListing.status == status)
    
    listings = query.order_by(DBListing.created_at.desc()).all()
    return listings

@router.get("/stats/summary")
async def get_listings_summary(db: Session = Depends(get_db)):
    """Get summary statistics for listings"""
    total_listings = db.query(DBListing).count()
    active_listings = db.query(DBListing).filter(DBListing.status == "Active").count()
    pending_listings = db.query(DBListing).filter(DBListing.status == "Pending").count()
    sold_listings = db.query(DBListing).filter(DBListing.status == "Sold").count()
    
    # Average price calculation
    avg_price_result = db.query(db.func.avg(DBListing.price)).filter(
        DBListing.status == "Active"
    ).scalar()
    avg_price = float(avg_price_result) if avg_price_result else 0.0
    
    # Price ranges
    price_ranges = {
        "under_500k": db.query(DBListing).filter(
            DBListing.price < 500000,
            DBListing.status == "Active"
        ).count(),
        "500k_to_1m": db.query(DBListing).filter(
            DBListing.price >= 500000,
            DBListing.price < 1000000,
            DBListing.status == "Active"
        ).count(),
        "over_1m": db.query(DBListing).filter(
            DBListing.price >= 1000000,
            DBListing.status == "Active"
        ).count()
    }
    
    return {
        "total_listings": total_listings,
        "active_listings": active_listings,
        "pending_listings": pending_listings,
        "sold_listings": sold_listings,
        "average_price": avg_price,
        "price_distribution": price_ranges
    }
