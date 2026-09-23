# Copyright 2026 Google LLC
# Seed script for ZenithFlow Firestore Collections

import datetime
from google.cloud import firestore

# IMPORTANT: Hardcoded Project ID as required
FIRESTORE_PROJECT_ID = "qwiklabs-gcp-01-f4e5d96ca16d"

def seed_firestore():
    print(f"Connecting to Firestore with project ID: '{FIRESTORE_PROJECT_ID}'...")
    db = firestore.Client(project=FIRESTORE_PROJECT_ID)

    # 1. Seed wellness_logs collection
    logs_ref = db.collection("wellness_logs")
    wellness_data = [
        {
            "id": "log_001",
            "date": "2026-09-20T10:00:00Z",
            "screen_time_hours": 7.5,
            "fatigue_score": 75,
            "primary_symptoms": ["eye_strain", "mental_fog"],
            "activity_suggested": "20-20-20 Eye Palming & Ocular Rest",
            "hydration_ml_needed": 2500,
            "notes": "Heavy debugging session on complex microservices architecture.",
        },
        {
            "id": "log_002",
            "date": "2026-09-21T14:30:00Z",
            "screen_time_hours": 8.0,
            "fatigue_score": 85,
            "primary_symptoms": ["tension_headache", "neck_stiffness"],
            "activity_suggested": "Suboccipital Release & Temple Acupressure",
            "hydration_ml_needed": 3000,
            "notes": "Extended screen hours with tight deadline and minimal breaks.",
        },
        {
            "id": "log_003",
            "date": "2026-09-22T11:15:00Z",
            "screen_time_hours": 6.0,
            "fatigue_score": 60,
            "primary_symptoms": ["wrist_pain", "lower_back_stiffness"],
            "activity_suggested": "Wrist Flexor & Thoracic Spine Decompression",
            "hydration_ml_needed": 2200,
            "notes": "Long refactoring sprint with mechanical keyboard.",
        },
        {
            "id": "log_004",
            "date": "2026-09-23T16:00:00Z",
            "screen_time_hours": 9.0,
            "fatigue_score": 90,
            "primary_symptoms": ["eye_strain", "tension_headache", "neck_stiffness"],
            "activity_suggested": "Seated Neck Traction & Shoulder Decompression",
            "hydration_ml_needed": 3200,
            "notes": "Late night production deployment review and code audit.",
        },
    ]

    for log in wellness_data:
        doc_id = log["id"]
        doc_data = {k: v for k, v in log.items() if k != "id"}
        logs_ref.document(doc_id).set(doc_data)
        print(f"Seeded wellness_logs record: {doc_id}")

    # 2. Seed routines_library collection
    routines_ref = db.collection("routines_library")
    routines_data = [
        {
            "id": "routine_001",
            "routine_name": "20-20-20 Eye Palming & Ocular Rest",
            "target_category": "Eye Care & Headaches",
            "duration_minutes": 5,
            "instructions": [
                "Look away from screen at an object 20 feet away for 20 seconds.",
                "Rub palms together briskly until warm and gently cup over closed eyes without pressing the eyelids.",
                "Breathe deeply for 5 slow breaths while absorbing the warmth.",
                "Slowly roll eyes clockwise 3 times and counter-clockwise 3 times.",
            ],
            "relief_benefits": "Reduces digital eye strain, relaxes ciliary eye muscles, and alleviates tension around optic nerves.",
        },
        {
            "id": "routine_002",
            "routine_name": "Suboccipital Release & Temple Acupressure",
            "target_category": "Eye Care & Headaches",
            "duration_minutes": 7,
            "instructions": [
                "Place index and middle fingers on your temples and apply gentle circular pressure for 60 seconds.",
                "Locate the base of your skull (suboccipital ridge) with your thumbs.",
                "Tilt head slightly back while pressing thumbs upward under the ridge for 45 seconds.",
                "Perform 5 slow chin tucks, drawing the head straight back without tilting down.",
            ],
            "relief_benefits": "Relieves tension headaches, eases occipital nerve compression, and reduces neck stiffness.",
        },
        {
            "id": "routine_003",
            "routine_name": "Seated Neck Traction & Shoulder Decompression",
            "target_category": "Upper Body Ergonomics",
            "duration_minutes": 8,
            "instructions": [
                "Sit upright in chair with feet flat on the floor.",
                "Hold the bottom of your seat with your right hand, and lean head gently to the left.",
                "Place left hand on right temple to add minimal, gentle traction for 30 seconds.",
                "Repeat on the opposite side.",
                "Perform 10 backward shoulder rolls while inhaling deeply.",
            ],
            "relief_benefits": "Decompresses cervical spine, opens tight upper trapezius muscles, and restores neck mobility.",
        },
        {
            "id": "routine_004",
            "routine_name": "Wrist Flexor & Thoracic Spine Decompression",
            "target_category": "Full Body Stretch",
            "duration_minutes": 10,
            "instructions": [
                "Extend right arm forward, palm up. Pull fingers back toward shoulder with left hand for 30 seconds.",
                "Flip right hand palm down, pull knuckles back toward chest for 30 seconds. Repeat on left arm.",
                "Interlace fingers behind lower back, straighten arms, and roll shoulders back to open chest.",
                "Perform 5 seated cat-cow arches using your desk for support.",
            ],
            "relief_benefits": "Prevents carpal tunnel syndrome, alleviates wrist tendon fatigue, and corrects slouching posture.",
        },
    ]

    for routine in routines_data:
        doc_id = routine["id"]
        doc_data = {k: v for k, v in routine.items() if k != "id"}
        routines_ref.document(doc_id).set(doc_data)
        print(f"Seeded routines_library record: {doc_id}")

    print("Firestore seeding completed successfully!")

if __name__ == "__main__":
    seed_firestore()
