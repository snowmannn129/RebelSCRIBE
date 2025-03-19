print("Starting import check...")

try:
    print("Importing StatisticsService...")
    from backend.services.statistics_service import StatisticsService
    print("Successfully imported StatisticsService")
    
    print("Creating StatisticsService instance...")
    service = StatisticsService()
    print("Successfully created StatisticsService instance")
    
    print("Testing _update_goal_progress method...")
    from backend.models.document import Document
    from dataclasses import dataclass, field
    
    # Create a test goal
    from backend.services.statistics_service import WritingGoal
    goal = WritingGoal(
        id="test_goal",
        name="Test Goal",
        target_type="words",
        target_value=500,
        start_date=None
    )
    
    # Call the method
    service._update_goal_progress(goal)
    print(f"Goal progress updated: current_value={goal.current_value}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("Import check complete")
