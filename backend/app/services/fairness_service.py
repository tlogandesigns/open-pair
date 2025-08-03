from typing import List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.database_models import Agent, OpenHouse, AgentRecommendation
from app.models.schemas import AgentScoreDetails

class FairnessService:
    """Ensures fair distribution of open house opportunities among agents"""
    
    def __init__(self):
        self.min_opportunities_per_month = {
            "junior": 2,    # < 2 years experience
            "mid": 3,       # 2-5 years experience  
            "senior": 4     # 5+ years experience
        }
        self.max_opportunities_per_month = {
            "junior": 8,
            "mid": 12,
            "senior": 16
        }
    
    def get_agent_tier(self, agent: Agent) -> str:
        """Determine agent experience tier"""
        if agent.experience_years < 2:
            return "junior"
        elif agent.experience_years < 5:
            return "mid"
        else:
            return "senior"
    
    def get_opportunity_counts(self, agent_id: int, reference_date: datetime, db: Session) -> Dict[str, int]:
        """Get agent's opportunity counts for fairness calculations"""
        thirty_days_ago = reference_date - timedelta(days=30)
        ninety_days_ago = reference_date - timedelta(days=90)
        
        # Count opportunities in last 30 days
        last_30_days = db.query(OpenHouse).filter(
            OpenHouse.host_agent_id == agent_id,
            OpenHouse.start_time >= thirty_days_ago,
            OpenHouse.start_time <= reference_date
        ).count()
        
        # Count opportunities in last 90 days
        last_90_days = db.query(OpenHouse).filter(
            OpenHouse.host_agent_id == agent_id,
            OpenHouse.start_time >= ninety_days_ago,
            OpenHouse.start_time <= reference_date
        ).count()
        
        # Count recommendations (whether selected or not)
        recommendations_30_days = db.query(AgentRecommendation).join(OpenHouse).filter(
            AgentRecommendation.agent_id == agent_id,
            OpenHouse.start_time >= thirty_days_ago,
            OpenHouse.start_time <= reference_date
        ).count()
        
        return {
            "hosted_30_days": last_30_days,
            "hosted_90_days": last_90_days,
            "recommended_30_days": recommendations_30_days
        }
    
    def calculate_fairness_score(self, agent: Agent, reference_date: datetime, db: Session) -> float:
        """Calculate fairness score (higher = more deserving of opportunity)"""
        tier = self.get_agent_tier(agent)
        counts = self.get_opportunity_counts(agent.id, reference_date, db)
        
        # Base fairness score
        fairness_score = 0.5
        
        # Boost for agents below minimum opportunities
        min_opportunities = self.min_opportunities_per_month[tier]
        if counts["hosted_30_days"] < min_opportunities:
            deficit = min_opportunities - counts["hosted_30_days"]
            fairness_score += deficit * 0.15  # 15% boost per missing opportunity
        
        # Penalty for agents above maximum opportunities
        max_opportunities = self.max_opportunities_per_month[tier]
        if counts["hosted_30_days"] > max_opportunities:
            excess = counts["hosted_30_days"] - max_opportunities
            fairness_score -= excess * 0.1  # 10% penalty per excess opportunity
        
        # Boost for agents with few recommendations (not just hosting)
        if counts["recommended_30_days"] < 5:
            fairness_score += 0.1
        
        # Time since last opportunity boost
        last_hosted = db.query(OpenHouse).filter(
            OpenHouse.host_agent_id == agent.id,
            OpenHouse.status.in_(["Completed", "Scheduled"])
        ).order_by(OpenHouse.start_time.desc()).first()
        
        if last_hosted:
            days_since_last = (reference_date - last_hosted.start_time).days
            if days_since_last > 14:  # More than 2 weeks ago
                fairness_score += min(days_since_last * 0.01, 0.2)  # Up to 20% boost
        else:
            # Never hosted - significant boost for new agents
            fairness_score += 0.3
        
        return min(max(fairness_score, 0.0), 1.0)
    
    def apply_fairness_adjustments(self, agent_scores: List[AgentScoreDetails], 
                                 reference_date: datetime, db: Session) -> List[AgentScoreDetails]:
        """Apply fairness adjustments to agent scores"""
        adjusted_scores = []
        
        for score_detail in agent_scores:
            agent = db.query(Agent).filter(Agent.id == score_detail.agent_id).first()
            if not agent:
                continue
            
            fairness_score = self.calculate_fairness_score(agent, reference_date, db)
            
            # Combine original ML score with fairness score
            # 70% ML score, 30% fairness consideration
            adjusted_score = (score_detail.score * 0.7) + (fairness_score * 0.3)
            
            # Update reasoning to include fairness factors
            tier = self.get_agent_tier(agent)
            counts = self.get_opportunity_counts(agent.id, reference_date, db)
            
            fairness_reasoning = []
            if counts["hosted_30_days"] < self.min_opportunities_per_month[tier]:
                fairness_reasoning.append("Below minimum monthly opportunities")
            if counts["recommended_30_days"] < 5:
                fairness_reasoning.append("Few recent recommendations")
            
            # Add fairness info to reasoning
            updated_reasoning = score_detail.reasoning.copy()
            updated_reasoning["fairness_score"] = fairness_score
            updated_reasoning["fairness_factors"] = fairness_reasoning
            updated_reasoning["opportunities_30_days"] = counts["hosted_30_days"]
            updated_reasoning["agent_tier"] = tier
            
            adjusted_scores.append(AgentScoreDetails(
                agent_id=score_detail.agent_id,
                agent_name=score_detail.agent_name,
                score=adjusted_score,
                confidence=score_detail.confidence,
                reasoning=updated_reasoning,
                availability_confirmed=score_detail.availability_confirmed
            ))
        
        # Re-sort by adjusted scores
        adjusted_scores.sort(key=lambda x: x.score, reverse=True)
        return adjusted_scores
    
    def ensure_diversity_in_recommendations(self, agent_scores: List[AgentScoreDetails], 
                                          db: Session) -> List[AgentScoreDetails]:
        """Ensure diversity in the top recommendations"""
        if len(agent_scores) <= 3:
            return agent_scores
        
        diverse_recommendations = []
        used_tiers = set()
        
        # First pass: ensure we have at least one agent from each tier if possible
        for score_detail in agent_scores:
            agent = db.query(Agent).filter(Agent.id == score_detail.agent_id).first()
            if agent:
                tier = self.get_agent_tier(agent)
                if tier not in used_tiers and len(diverse_recommendations) < 3:
                    diverse_recommendations.append(score_detail)
                    used_tiers.add(tier)
        
        # Second pass: fill remaining slots with highest scores
        for score_detail in agent_scores:
            if score_detail not in diverse_recommendations and len(diverse_recommendations) < 3:
                diverse_recommendations.append(score_detail)
        
        # If we still need more, add the highest remaining scores
        remaining_slots = 3 - len(diverse_recommendations)
        for i, score_detail in enumerate(agent_scores):
            if score_detail not in diverse_recommendations and i < remaining_slots:
                diverse_recommendations.append(score_detail)
        
        return diverse_recommendations[:3]
    
    def get_fairness_report(self, reference_date: datetime, db: Session) -> Dict[str, Any]:
        """Generate a fairness report for all agents"""
        agents = db.query(Agent).filter(Agent.is_active == True).all()
        
        report = {
            "report_date": reference_date,
            "agents": [],
            "summary": {
                "total_active_agents": len(agents),
                "agents_below_minimum": 0,
                "agents_above_maximum": 0,
                "tier_distribution": {"junior": 0, "mid": 0, "senior": 0}
            }
        }
        
        for agent in agents:
            tier = self.get_agent_tier(agent)
            counts = self.get_opportunity_counts(agent.id, reference_date, db)
            fairness_score = self.calculate_fairness_score(agent, reference_date, db)
            
            min_opp = self.min_opportunities_per_month[tier]
            max_opp = self.max_opportunities_per_month[tier]
            
            agent_report = {
                "agent_id": agent.id,
                "agent_name": agent.name,
                "tier": tier,
                "opportunities_30_days": counts["hosted_30_days"],
                "recommendations_30_days": counts["recommended_30_days"],
                "fairness_score": fairness_score,
                "status": "balanced"
            }
            
            if counts["hosted_30_days"] < min_opp:
                agent_report["status"] = "below_minimum"
                report["summary"]["agents_below_minimum"] += 1
            elif counts["hosted_30_days"] > max_opp:
                agent_report["status"] = "above_maximum"
                report["summary"]["agents_above_maximum"] += 1
            
            report["agents"].append(agent_report)
            report["summary"]["tier_distribution"][tier] += 1
        
        # Sort by fairness score (highest first - most deserving)
        report["agents"].sort(key=lambda x: x["fairness_score"], reverse=True)
        
        return report

# Global instance
fairness_service = FairnessService()
