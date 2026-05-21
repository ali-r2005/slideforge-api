import json
import os
from pathlib import Path


class TeamBuildingService:
    """Service to load and manage team building activities from database."""

    _instance = None
    _activities = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._activities is None:
            self._activities = self._load_activities()

    def _load_activities(self):
        """Load team building activities from db.json."""
        try:
            # Path: /slideforge-api/DB/tb.json
            db_path = Path(__file__).parent.parent.parent / "DB" / "tb.json"

            if not db_path.exists():
                print(f"Team building database not found at: {db_path}")
                return []

            with open(db_path, 'r', encoding='utf-8') as f:
                activities = json.load(f)
                print(f"Loaded {len(activities)} team building activities")
                return activities
        except Exception as e:
            print(f"Error loading team building database: {e}")
            return []

    def get_all_activities(self):
        """Return all team building activities."""
        return self._activities

    def get_activity_by_id(self, activity_id: int):
        """Return a single activity by ID."""
        for activity in self._activities:
            if activity.get("id") == activity_id:
                return activity
        return None

    def reload_activities(self):
        """Reload activities from file (useful for testing)."""
        self._activities = self._load_activities()
        return self._activities


# Singleton instance
team_building_service = TeamBuildingService()
