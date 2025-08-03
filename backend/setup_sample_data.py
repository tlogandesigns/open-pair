#!/usr/bin/env python3
"""
Script to populate the database with sample data for development and testing
"""

import sys
import os
import json
from datetime import datetime, timedelta
import random

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__)))

from app.database.connection import SessionLocal, create_tables
from app.models.database_models import Agent, Listing, OpenHouse, AgentAvailability, AgentPerformance

def load_sample_agents(db):
    """Load sample agents from JSON file"""
    with open('../data/sample_agents.json', 'r') as f:
        agents_data = json.load(f)
    
    agents = []
    for agent_data in agents_data:
        agent = Agent(**agent_data)
        db.add(agent)
        agents.append(agent)
    
    db.commit()
    
    # Refresh to get IDs
    for agent in agents:
        db.refresh(agent)
    
    print(f"Created {len(agents)} sample agents")
    return agents

def load_sample_listings(db, agents):
    """Load sample listings from JSON file"""
    with open('../data/sample_listings.json', 'r') as f:
        listings_data = json.load(f)
    
    listings = []
    for listing_data in listings_data:
        # Convert listing_date string to datetime
        if 'listing_date' in listing_data:
            listing_data['listing_date'] = datetime.fromisoformat(
                listing_data['listing_date'].replace('Z', '+00:00')
            )
        
        # Ensure listing agent exists
        if listing_data['listing_agent_id'] <= len(agents):
            listing = Listing(**listing_data)
            db.add(listing)
            listings.append(listing)
    
    db.commit()
    
    # Refresh to get IDs
    for listing in listings:
        db.refresh(listing)
    
    print(f"Created {len(listings)} sample listings")
    return listings

def create_agent_availability(db, agents):
    """Create sample availability schedules for agents"""
    days_of_week = [0, 1, 2, 3, 4, 5, 6]  # Monday to Sunday
    
    for agent in agents:
        # Most agents available on weekends
        for day in [5, 6]:  # Saturday, Sunday
            availability = AgentAvailability(
                agent_id=agent.id,
                day_of_week=day,
                start_time="09:00",
                end_time="17:00",
                is_recurring=True,
                is_available=True
            )
            db.add(availability)
        
        # Some agents also available on weekdays
        if random.random() > 0.3:  # 70% chance
            weekday = random.choice([1, 2, 3, 4])  # Tue, Wed, Thu, Fri
            availability = AgentAvailability(
                agent_id=agent.id,
                day_of_week=weekday,
                start_time="14:00",
                end_time="18:00",
                is_recurring=True,
                is_available=True
            )
            db.add(availability)
    
    db.commit()
    print(f"Created availability schedules for {len(agents)} agents")

def create_sample_open_houses(db, listings, agents):
    """Create sample open houses"""
    open_houses = []
    
    for i, listing in enumerate(listings):
        # Create 1-2 open houses per listing
        num_houses = random.choice([1, 2])
        
        for j in range(num_houses):
            # Schedule open house for next few weekends
            base_date = datetime.now() + timedelta(days=7 + (i * 2) + (j * 14))
            # Adjust to Saturday or Sunday
            base_date = base_date - timedelta(days=base_date.weekday()) + timedelta(days=5 + j)
            
            start_time = base_date.replace(hour=14, minute=0, second=0, microsecond=0)
            end_time = start_time + timedelta(hours=2)
            
            open_house = OpenHouse(
                listing_id=listing.id,
                scheduled_date=start_time.date(),
                start_time=start_time,
                end_time=end_time,
                status="Scheduled"
            )
            
            # Randomly assign some open houses to agents
            if random.random() > 0.4:  # 60% get assigned
                open_house.host_agent_id = random.choice(agents).id
            
            db.add(open_house)
            open_houses.append(open_house)
    
    db.commit()
    
    # Refresh to get IDs
    for oh in open_houses:
        db.refresh(oh)
    
    print(f"Created {len(open_houses)} sample open houses")
    return open_houses

def create_sample_performance_data(db, agents):
    """Create sample performance data for agents"""
    end_date = datetime.now()
    
    for agent in agents:
        # Create monthly performance records for last 6 months
        for month_offset in range(6):
            period_end = end_date - timedelta(days=month_offset * 30)
            period_start = period_end - timedelta(days=30)
            
            # Generate realistic performance metrics based on experience
            base_houses = max(1, agent.experience_years // 2)
            open_houses_hosted = random.randint(base_houses, base_houses + 3)
            
            total_attendees = sum(random.randint(8, 25) for _ in range(open_houses_hosted))
            total_leads = sum(random.randint(0, 6) for _ in range(open_houses_hosted))
            total_follow_ups = sum(random.randint(0, 4) for _ in range(open_houses_hosted))
            total_offers = sum(random.randint(0, 2) for _ in range(open_houses_hosted))
            
            conversion_rate = total_leads / max(total_attendees, 1)
            success_rate = total_offers / max(total_leads, 1)
            
            # Feedback score based on experience and random variation
            base_score = min(3.0 + (agent.experience_years * 0.1), 4.5)
            feedback_score = base_score + random.uniform(-0.5, 0.5)
            feedback_score = max(1.0, min(5.0, feedback_score))
            
            performance = AgentPerformance(
                agent_id=agent.id,
                period_start=period_start,
                period_end=period_end,
                open_houses_hosted=open_houses_hosted,
                total_attendees=total_attendees,
                total_leads=total_leads,
                total_follow_ups=total_follow_ups,
                total_offers=total_offers,
                conversion_rate=conversion_rate,
                success_rate=success_rate,
                average_feedback_score=feedback_score
            )
            db.add(performance)
    
    db.commit()
    print(f"Created performance data for {len(agents)} agents over 6 months")

def main():
    """Main function to set up sample data"""
    print("Setting up sample data for Open House Matchmaker...")
    
    # Create database tables
    create_tables()
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Load sample data
        agents = load_sample_agents(db)
        listings = load_sample_listings(db, agents)
        create_agent_availability(db, agents)
        open_houses = create_sample_open_houses(db, listings, agents)
        create_sample_performance_data(db, agents)
        
        print("\n✅ Sample data setup completed successfully!")
        print(f"   - {len(agents)} agents")
        print(f"   - {len(listings)} listings")
        print(f"   - {len(open_houses)} open houses")
        print(f"   - Availability schedules and performance data")
        
    except Exception as e:
        print(f"❌ Error setting up sample data: {e}")
        db.rollback()
        raise
    
    finally:
        db.close()

if __name__ == "__main__":
    main()
