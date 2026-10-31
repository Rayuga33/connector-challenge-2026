from src.services.analytics import (
    get_dashboard_metrics,
    get_monthly_rental_data,
    get_equipment_data,
    get_top_equipment
)

print("\n=== EQUIPINTEL ANALYTICS ===")

print("\nKEY METRICS")
for key, value in get_dashboard_metrics().items():
    print(f"{key}: {value}")

print("\nMONTHLY RENTAL VALUE")
for item in get_monthly_rental_data():
    print(item)

print("\nEQUIPMENT CATEGORIES")
for item in get_equipment_data():
    print(item)

print("\nTOP EQUIPMENT")
for item in get_top_equipment():
    print(item)