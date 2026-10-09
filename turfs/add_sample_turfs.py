from decimal import Decimal
from datetime import time

from django.contrib.auth import get_user_model
from turfs.models import Turf

User = get_user_model()

# Find an existing vendor account

vendor = User.objects.filter(role="VENDOR").first()

if vendor is None:
    print("ERROR: No vendor account found.")
    print("Please register a vendor account and run this script again.")
else:
    sample_turfs = [
{
"name": "Green Arena Turf",
"location": "Peelamedu, Coimbatore",
"description": "Well-maintained football turf for friends and teams.",
"price_per_hour": Decimal("1000.00"),
"facilities": "Floodlights, Parking, Changing Room",
"opening_time": time(6, 0),
"closing_time": time(22, 0),
},
{
"name": "Victory Sports Turf",
"location": "Gandhipuram, Coimbatore",
"description": "Spacious synthetic grass turf for football matches.",
"price_per_hour": Decimal("1200.00"),
"facilities": "Floodlights, Drinking Water, Parking",
"opening_time": time(5, 0),
"closing_time": time(23, 0),
},
{
"name": "Champion Football Ground",
"location": "RS Puram, Coimbatore",
"description": "A comfortable ground for practice and friendly matches.",
"price_per_hour": Decimal("900.00"),
"facilities": "Changing Room, Seating Area, Drinking Water",
"opening_time": time(6, 0),
"closing_time": time(21, 0),
},
{
"name": "Skyline Sports Arena",
"location": "Saravanampatti, Coimbatore",
"description": "Sports turf suitable for daytime and night matches.",
"price_per_hour": Decimal("1500.00"),
"facilities": "Floodlights, Parking, Rest Area",
"opening_time": time(5, 0),
"closing_time": time(23, 0),
},
{
"name": "PowerPlay Turf",
"location": "Singanallur, Coimbatore",
"description": "Affordable football turf for friends and group bookings.",
"price_per_hour": Decimal("800.00"),
"facilities": "Drinking Water, Parking, Seating Area",
"opening_time": time(6, 0),
"closing_time": time(22, 0),
},
]


added_count = 0

for turf_data in sample_turfs:
    turf, created = Turf.objects.get_or_create(
        name=turf_data["name"],
        location=turf_data["location"],
        defaults={
            **turf_data,
            "vendor": vendor,
            "is_available": True,
        },
    )

    if created:
        added_count += 1
        print(f"Added: {turf.name}")
    else:
        print(f"Already exists: {turf.name}")

print(f"\nCompleted! {added_count} new turf(s) added.")
print(f"Total sample turfs available: {Turf.objects.count()}")

