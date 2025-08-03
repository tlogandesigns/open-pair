#!/usr/bin/env python3
"""
Test script to validate module imports work correctly.
This simulates the container environment for testing.
"""

import sys
import os
from pathlib import Path

def test_imports():
    """Test that all required modules can be imported."""
    
    # Get the project root (where this script is located)
    project_root = Path(__file__).parent
    backend_path = project_root / "backend"
    
    # Add backend directory to Python path (simulating container environment)
    sys.path.insert(0, str(backend_path))
    
    print(f"Testing imports from: {backend_path}")
    print(f"Python path: {sys.path[:2]}")
    
    try:
        # Test main app import
        from main import app
        print("✓ Successfully imported main.app")
        
        # Test API modules
        from app.api import agents, listings, open_houses, dashboard
        print("✓ Successfully imported API modules")
        
        # Test database modules
        from app.database.connection import engine, create_tables
        print("✓ Successfully imported database modules")
        
        # Test models
        from app.models import agent, listing, open_house
        print("✓ Successfully imported model modules")
        
        # Test services
        from app.services import agent_matcher, fairness_engine
        print("✓ Successfully imported service modules")
        
        # Test ML modules
        from app.ml import agent_scorer
        print("✓ Successfully imported ML modules")
        
        print("\n🎉 All imports successful! The container should work correctly.")
        return True
        
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        print("\n🚨 There are import issues that need to be resolved.")
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
