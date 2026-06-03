"""
Database loading and validation utility.
Loads databases from DB/ directory and validates schema.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger(__name__)


class DatabaseLoader:
    """Loads and validates databases for dynamic schema configuration."""

    # Cache for loaded databases
    _cache: Dict[str, List[Dict]] = {}
    _errors: Dict[str, str] = {}

    @staticmethod
    def load_database(name: str, db_dir: str = "DB") -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Load and validate a database file.

        Args:
            name: Database name (e.g., "tb" for DB/tb.json)
            db_dir: Directory containing database files

        Returns:
            (items, error): Tuple of (database items list, error message)
            If successful: (list of items, None)
            If error: (None, error message)
        """
        # Check cache first
        if name in DatabaseLoader._cache:
            return DatabaseLoader._cache[name], None

        if name in DatabaseLoader._errors:
            return None, DatabaseLoader._errors[name]

        try:
            # Build path to database file
            db_path = Path(db_dir) / f"{name}.json"

            # Check if file exists
            if not db_path.exists():
                error_msg = f"Database '{name}' not found at {db_path}"
                DatabaseLoader._errors[name] = error_msg
                logger.error(error_msg)
                return None, error_msg

            # Load and parse JSON
            with open(db_path, "r", encoding="utf-8") as f:
                items = json.load(f)

            # Validate it's a list
            if not isinstance(items, list):
                error_msg = f"Database '{name}' must contain a JSON array at root level"
                DatabaseLoader._errors[name] = error_msg
                logger.error(error_msg)
                return None, error_msg

            # Check if empty
            if len(items) == 0:
                error_msg = f"Database '{name}' is empty (contains no items)"
                DatabaseLoader._errors[name] = error_msg
                logger.error(error_msg)
                return None, error_msg

            # Validate schema: all items must have id and name
            validation_error = DatabaseLoader.validate_database_items(items, name)
            if validation_error:
                DatabaseLoader._errors[name] = validation_error
                logger.error(validation_error)
                return None, validation_error

            # Cache the result
            DatabaseLoader._cache[name] = items
            logger.info(f"Loaded database '{name}' with {len(items)} items")
            return items, None

        except json.JSONDecodeError as e:
            error_msg = f"Database '{name}' is not valid JSON: {str(e)}"
            DatabaseLoader._errors[name] = error_msg
            logger.error(error_msg)
            return None, error_msg
        except Exception as e:
            error_msg = f"Error loading database '{name}': {str(e)}"
            DatabaseLoader._errors[name] = error_msg
            logger.error(error_msg)
            return None, error_msg

    @staticmethod
    def validate_database_items(items: List[Dict], name: str) -> Optional[str]:
        """
        Validate that database items have required fields (id and name).

        Args:
            items: List of database items
            name: Database name (for error messages)

        Returns:
            Error message if validation fails, None if valid
        """
        if not items:
            return f"Database '{name}' contains no items"

        # Check first item for required fields
        first_item = items[0]

        if "id" not in first_item:
            return f"Database '{name}' is missing required 'id' field in item: {first_item}"

        if "name" not in first_item:
            return f"Database '{name}' is missing required 'name' field in item: {first_item}"

        # Check that id and name are not null
        if first_item["id"] is None:
            return f"Database '{name}' has null 'id' in item: {first_item}"

        if first_item["name"] is None or str(first_item["name"]).strip() == "":
            return f"Database '{name}' has null or empty 'name' in item: {first_item}"

        return None

    @staticmethod
    def get_database_options(name: str, db_dir: str = "DB") -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
        """
        Get database items formatted for frontend select options.

        Args:
            name: Database name
            db_dir: Database directory

        Returns:
            (options, error): List of {id, name} dicts or error message
        """
        items, error = DatabaseLoader.load_database(name, db_dir)

        if error:
            return None, error

        # Extract only id and name fields for frontend
        options = [{"id": item["id"], "name": item["name"]} for item in items]
        return options, None

    @staticmethod
    def clear_cache():
        """Clear the database cache (useful for testing)."""
        DatabaseLoader._cache.clear()
        DatabaseLoader._errors.clear()

    @staticmethod
    def get_cached_databases() -> List[str]:
        """Get list of cached database names."""
        return list(DatabaseLoader._cache.keys())
