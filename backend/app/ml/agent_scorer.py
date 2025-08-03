import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
import xgboost as xgb
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sqlalchemy.orm import Session
from app.models.database_models import Agent, OpenHouse, AgentPerformance, Listing, AgentRecommendation
from app.models.schemas import AgentScoreDetails
import pickle
import os

class AgentScoringEngine:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self.model_version = "1.0.0"
        self.model_path = "app/ml/models/"
        os.makedirs(self.model_path, exist_ok=True)
        
    def extract_features(self, agent: Agent, listing: Listing, open_house_datetime: datetime, db: Session) -> Dict[str, float]:
        """Extract features for agent scoring"""
        features = {}
        
        # Agent basic features
        features['experience_years'] = agent.experience_years
        features['is_active'] = 1.0 if agent.is_active else 0.0
        
        # Performance metrics (last 12 months)
        twelve_months_ago = open_house_datetime - timedelta(days=365)
        performance = db.query(AgentPerformance).filter(
            AgentPerformance.agent_id == agent.id,
            AgentPerformance.period_start >= twelve_months_ago
        ).all()
        
        if performance:
            # Aggregate performance metrics
            total_hosted = sum(p.open_houses_hosted for p in performance)
            total_attendees = sum(p.total_attendees for p in performance)
            total_leads = sum(p.total_leads for p in performance)
            total_offers = sum(p.total_offers for p in performance)
            avg_feedback = np.mean([p.average_feedback_score for p in performance if p.average_feedback_score > 0])
            
            features['total_open_houses_hosted'] = total_hosted
            features['avg_attendees_per_event'] = total_attendees / max(total_hosted, 1)
            features['conversion_rate'] = total_leads / max(total_attendees, 1)
            features['success_rate'] = total_offers / max(total_leads, 1)
            features['average_feedback_score'] = avg_feedback if not np.isnan(avg_feedback) else 3.0
        else:
            # Default values for new agents
            features['total_open_houses_hosted'] = 0
            features['avg_attendees_per_event'] = 0
            features['conversion_rate'] = 0
            features['success_rate'] = 0
            features['average_feedback_score'] = 3.0
        
        # Area familiarity
        agent_areas = agent.areas_of_expertise or []
        features['area_familiarity'] = 1.0 if listing.zip_code in agent_areas else 0.0
        
        # Price range alignment
        buyer_ranges = agent.buyer_price_ranges or []
        price_match = 0.0
        for price_range in buyer_ranges:
            if 'min' in price_range and 'max' in price_range:
                if price_range['min'] <= listing.price <= price_range['max']:
                    price_match = 1.0
                    break
        features['price_range_match'] = price_match
        
        # Recency of activity
        recent_activity = db.query(OpenHouse).filter(
            OpenHouse.host_agent_id == agent.id,
            OpenHouse.start_time >= open_house_datetime - timedelta(days=30),
            OpenHouse.status == "Completed"
        ).count()
        features['recent_activity'] = recent_activity
        
        # Fair rotation factors
        last_30_days_hosted = db.query(OpenHouse).filter(
            OpenHouse.host_agent_id == agent.id,
            OpenHouse.start_time >= open_house_datetime - timedelta(days=30)
        ).count()
        features['recent_hosting_frequency'] = last_30_days_hosted
        
        # Experience tier for fairness
        if agent.experience_years < 2:
            features['experience_tier'] = 1.0  # Junior
        elif agent.experience_years < 5:
            features['experience_tier'] = 2.0  # Mid-level
        else:
            features['experience_tier'] = 3.0  # Senior
        
        return features
    
    def prepare_training_data(self, db: Session) -> Tuple[pd.DataFrame, pd.Series]:
        """Prepare training data from historical open houses"""
        training_data = []
        
        # Get completed open houses with recommendations
        completed_houses = db.query(OpenHouse).filter(
            OpenHouse.status == "Completed"
        ).all()
        
        for open_house in completed_houses:
            if not open_house.listing:
                continue
                
            # Get all recommendations for this open house
            recommendations = db.query(AgentRecommendation).filter(
                AgentRecommendation.open_house_id == open_house.id
            ).all()
            
            for rec in recommendations:
                agent = db.query(Agent).filter(Agent.id == rec.agent_id).first()
                if not agent:
                    continue
                
                features = self.extract_features(agent, open_house.listing, open_house.start_time, db)
                
                # Target: success score based on actual outcomes
                success_score = self.calculate_success_score(open_house, rec.was_selected)
                
                row = features.copy()
                row['target'] = success_score
                row['was_selected'] = rec.was_selected
                training_data.append(row)
        
        if not training_data:
            # Return dummy data if no training data available
            dummy_features = {
                'experience_years': 0, 'is_active': 1, 'total_open_houses_hosted': 0,
                'avg_attendees_per_event': 0, 'conversion_rate': 0, 'success_rate': 0,
                'average_feedback_score': 3.0, 'area_familiarity': 0, 'price_range_match': 0,
                'recent_activity': 0, 'recent_hosting_frequency': 0, 'experience_tier': 1.0,
                'target': 0.5
            }
            training_data = [dummy_features]
        
        df = pd.DataFrame(training_data)
        X = df.drop(['target', 'was_selected'], axis=1, errors='ignore')
        y = df['target']
        
        self.feature_names = list(X.columns)
        return X, y
    
    def calculate_success_score(self, open_house: OpenHouse, was_selected: bool) -> float:
        """Calculate success score based on open house outcomes"""
        if not was_selected:
            return 0.0
        
        # Normalize metrics to 0-1 scale
        attendee_score = min(open_house.attendee_count / 20.0, 1.0)  # 20+ attendees = perfect
        lead_score = min(open_house.leads_generated / 5.0, 1.0)  # 5+ leads = perfect
        follow_up_score = min(open_house.follow_ups_scheduled / 3.0, 1.0)  # 3+ follow-ups = perfect
        offer_score = min(open_house.offers_received / 1.0, 1.0)  # 1+ offer = perfect
        
        # Weighted combination
        success_score = (
            attendee_score * 0.2 +
            lead_score * 0.3 +
            follow_up_score * 0.3 +
            offer_score * 0.2
        )
        
        return min(success_score, 1.0)
    
    def train_model(self, db: Session) -> Dict[str, Any]:
        """Train the XGBoost model"""
        X, y = self.prepare_training_data(db)
        
        if len(X) < 10:  # Not enough data for proper training
            # Create a simple rule-based model for cold start
            self.model = "rule_based"
            return {"model_type": "rule_based", "training_samples": len(X)}
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train XGBoost model
        model_params = {
            'objective': 'reg:squarederror',
            'max_depth': 6,
            'learning_rate': 0.1,
            'n_estimators': 100,
            'random_state': 42
        }
        
        self.model = xgb.XGBRegressor(**model_params)
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate model
        train_score = self.model.score(X_train_scaled, y_train)
        test_score = self.model.score(X_test_scaled, y_test)
        
        # Save model
        self.save_model()
        
        return {
            "model_type": "xgboost",
            "training_samples": len(X_train),
            "test_samples": len(X_test),
            "train_r2": train_score,
            "test_r2": test_score,
            "features": self.feature_names
        }
    
    def score_agents(self, agents: List[Agent], listing: Listing, open_house_datetime: datetime, db: Session) -> List[AgentScoreDetails]:
        """Score all available agents for an open house"""
        scores = []
        
        for agent in agents:
            features = self.extract_features(agent, listing, open_house_datetime, db)
            
            if self.model == "rule_based" or self.model is None:
                # Rule-based scoring for cold start
                score = self.rule_based_score(features)
            else:
                # ML-based scoring
                feature_vector = [features.get(name, 0) for name in self.feature_names]
                feature_vector_scaled = self.scaler.transform([feature_vector])
                score = float(self.model.predict(feature_vector_scaled)[0])
            
            # Apply fairness adjustments
            score = self.apply_fairness_adjustments(score, features, agent)
            
            # Generate reasoning
            reasoning = self.generate_reasoning(features, score)
            
            scores.append(AgentScoreDetails(
                agent_id=agent.id,
                agent_name=agent.name,
                score=score,
                confidence=min(score + 0.1, 1.0),  # Simple confidence estimate
                reasoning=reasoning,
                availability_confirmed=True  # TODO: Integrate with calendar API
            ))
        
        # Sort by score and return top candidates
        scores.sort(key=lambda x: x.score, reverse=True)
        return scores
    
    def rule_based_score(self, features: Dict[str, float]) -> float:
        """Simple rule-based scoring for cold start"""
        score = 0.5  # Base score
        
        # Experience bonus
        score += features['experience_years'] * 0.02
        
        # Performance bonuses
        score += features['conversion_rate'] * 0.3
        score += features['success_rate'] * 0.2
        score += (features['average_feedback_score'] - 3.0) * 0.1
        
        # Area and price match bonuses
        score += features['area_familiarity'] * 0.15
        score += features['price_range_match'] * 0.1
        
        # Recent activity bonus
        score += min(features['recent_activity'] * 0.05, 0.1)
        
        return min(max(score, 0.0), 1.0)
    
    def apply_fairness_adjustments(self, score: float, features: Dict[str, float], agent: Agent) -> float:
        """Apply fairness adjustments to prevent overloading top agents"""
        adjusted_score = score
        
        # Reduce score for agents with high recent hosting frequency
        if features['recent_hosting_frequency'] > 3:
            adjusted_score *= 0.8
        elif features['recent_hosting_frequency'] > 5:
            adjusted_score *= 0.6
        
        # Boost score for junior agents (opportunity distribution)
        if features['experience_tier'] == 1.0 and features['total_open_houses_hosted'] < 5:
            adjusted_score += 0.1
        
        return min(max(adjusted_score, 0.0), 1.0)
    
    def generate_reasoning(self, features: Dict[str, float], score: float) -> Dict[str, Any]:
        """Generate explanation for the agent recommendation"""
        reasons = []
        
        if features['conversion_rate'] > 0.1:
            reasons.append(f"Strong conversion rate: {features['conversion_rate']:.1%}")
        
        if features['area_familiarity'] > 0:
            reasons.append("Familiar with property area")
        
        if features['price_range_match'] > 0:
            reasons.append("Matches buyer price range")
        
        if features['average_feedback_score'] > 4.0:
            reasons.append(f"High feedback score: {features['average_feedback_score']:.1f}/5")
        
        if features['experience_years'] > 5:
            reasons.append(f"Experienced agent: {int(features['experience_years'])} years")
        
        if features['recent_hosting_frequency'] > 3:
            reasons.append("Note: High recent activity (fairness consideration)")
        
        return {
            "score": score,
            "key_factors": reasons[:3],  # Top 3 reasons
            "experience_years": int(features['experience_years']),
            "conversion_rate": features['conversion_rate'],
            "area_familiarity": features['area_familiarity'] > 0,
            "recent_activity": int(features['recent_activity'])
        }
    
    def save_model(self):
        """Save the trained model to disk"""
        if self.model and self.model != "rule_based":
            model_file = os.path.join(self.model_path, f"agent_scorer_{self.model_version}.pkl")
            scaler_file = os.path.join(self.model_path, f"scaler_{self.model_version}.pkl")
            
            with open(model_file, 'wb') as f:
                pickle.dump({
                    'model': self.model,
                    'feature_names': self.feature_names,
                    'model_version': self.model_version
                }, f)
            
            with open(scaler_file, 'wb') as f:
                pickle.dump(self.scaler, f)
    
    def load_model(self, version: str = None):
        """Load a trained model from disk"""
        version = version or self.model_version
        model_file = os.path.join(self.model_path, f"agent_scorer_{version}.pkl")
        scaler_file = os.path.join(self.model_path, f"scaler_{version}.pkl")
        
        try:
            if os.path.exists(model_file) and os.path.exists(scaler_file):
                with open(model_file, 'rb') as f:
                    model_data = pickle.load(f)
                    self.model = model_data['model']
                    self.feature_names = model_data['feature_names']
                    self.model_version = model_data['model_version']
                
                with open(scaler_file, 'rb') as f:
                    self.scaler = pickle.load(f)
                
                return True
        except Exception as e:
            print(f"Error loading model: {e}")
        
        return False

# Global instance
agent_scorer = AgentScoringEngine()
