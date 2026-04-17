from datetime import datetime, timezone
from typing import Optional
from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse
import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from helper.helper import (
    call_agify,
    call_genderize,
    call_nationalize,
    determin_age_group,
)
from schama.profile import ProfileCreate
from database.database import get_db, engine, Base
from database.model import Profile, generate_uuid7
import asyncio

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.post("/api/profiles", status_code=201)
async def create_profile(profile: ProfileCreate, db: Session = Depends(get_db)):

    if not profile.name or profile.name.strip() == "":
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "Missing or empty name"},
        )
    if not isinstance(profile.name, str):
        return JSONResponse(
            status_code=422,
            content={"status": "error", "message": "Name must be a String"},
        )

    normalized_name = profile.name.strip().lower()

    existing_profile = db.query(Profile).filter(Profile.name == normalized_name).first()
    if existing_profile:
        return {
            "status": "success",
            "message": "Profile already exists",
            "data": {
                "id": existing_profile.id,
                "name": existing_profile.name,
                "gender": existing_profile.gender,
                "gender_probability": existing_profile.gender_probability,
                "sample_size": existing_profile.sample_size,
                "age": existing_profile.age,
                "age_group": existing_profile.age_group,
                "country_id": existing_profile.country_id,
                "country_probability": existing_profile.country_probability,
                "created_at": existing_profile.created_at.isoformat().replace(
                    "+00:00", "Z"
                ),
            },
        }
    try:
        # gender_task = call_genderize(normalized_name)
        # age_task = call_agify(normalized_name)
        # country_task = call_nationalize(normalized_name)

        # gender_data, age_data, country_data = await asyncio.gather(
        #     gender_task, age_task, country_task
        # )
        with httpx.Client(timeout=10.0) as client:
            # Gendarize
            g_response = client.get(
                "https://api.genderize.io", params={"name": normalized_name}
            )
           
            g_data = g_response.json()

            # Agify
            a_response = client.get(
                "https://api.agify.io", params={"name": normalized_name}
            )
            a_data = a_response.json()

            # Nationalize
            n_response = client.get(
                "https://api.nationalize.io", params={"name": normalized_name}
            )
            n_data = n_response.json()
            # Validate responses
        if g_data.get("gender") is None or g_data.get("count") == 0:
            return JSONResponse(
                status_code=502,
                content={
                    "status": "502",
                    "message": "Genderize returned an invalid response",
                },
            )
        if a_data.get("age") is None:
            return JSONResponse(
                status_code=502,
                content={
                    "status": "502",
                    "message": "Agify returned an invalid response",
                },
            )

        if not n_data.get("country") or len(n_data["country"]) == 0:
            return JSONResponse(
                status_code=502,
                content={
                    "status": "502",
                    "message": "Nationalize returned an invalid response",
                },
            )

        # Get top country
        top_country = max(n_data["country"], key=lambda x: x["probability"])

        profile_id = generate_uuid7()
        new_profile = Profile(
            id=profile_id,
            name=normalized_name,
            gender=g_data["gender"],
            gender_probability=g_data["probability"],
            sample_size=g_data["count"],
            age=a_data["age"],
            age_group=determin_age_group(a_data["age"]),
            country_id=top_country["country_id"],
            country_probability=top_country["probability"],
            created_at=datetime.now(timezone.utc),
        )
        db.add(new_profile)
        db.commit()
        db.refresh(new_profile)

        return {
            "status": "success",
            "data": {
                "id": new_profile.id,
                "name": new_profile.name,
                "gender": new_profile.gender,
                "gender_probability": new_profile.gender_probability,
                "sample_size": new_profile.sample_size,
                "age": new_profile.age,
                "age_group": new_profile.age_group,
                "country_id": new_profile.country_id,
                "country_probability": new_profile.country_probability,
                "created_at": new_profile.created_at.isoformat().replace("+00:00", "Z"),
            },
        }

    except httpx.TimeoutException:
        return JSONResponse(
            status_code=504,
            content={"status": "error", "message": "External API timeout"},
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"Internal server error: {str(e)}"},
        )


@app.get("/api/profiles", status_code=200)
def list_profiles(
    gender: Optional[str]=None,
    country_id: Optional[str]=None,
    age_group: Optional[str]=None,
    db: Session = Depends(get_db),
):
    query = db.query(Profile)
    if gender:
        query.filter(Profile.gender == gender.lower())
    if country_id:
        query.filter(Profile.country_id == country_id.lower())
    if age_group:
        query.filter(Profile.age_group == age_group.lower())
    profiles = query.order_by(Profile.created_at.desc()).all()

    return {
        "status": "success",
        "count": len(profiles),
        "data": [
            {
                "id": p.id,
                "name": p.name,
                "gender": p.gender,
                "age": p.age,
                "age_group": p.age_group,
                "country_id": p.country_id,
            }
            for p in profiles
        ],
    }


@app.get("/api/profiles/{profile_id}", status_code=200)
def get_profile(profile_id: str, db: Session = Depends(get_db)):
    profile = db.query(Profile).filter(Profile.id == profile_id).first()

    if not profile:
        return JSONResponse(
            status_code=404, content={"status": "error", "message": "profile not found"}
        )
    return {
        "status": "success",
        "data": {
            "id": profile.id,
            "name": profile.name,
            "gender": profile.gender,
            "gender_probability": profile.gender_probability,
            "sample_size": profile.sample_size,
            "age": profile.age,
            "age_group": profile.age_group,
            "country_id": profile.country_id,
            "country_probability": profile.country_probability,
            "created_at": profile.created_at.isoformat().replace("+00:00", "Z"),
        },
    }


@app.delete("/api/profiles/{profile_id}", status_code=204)
def delete_profile(profile_id: str, db: Session = Depends(get_db)):
    profile = db.query(Profile).filter(Profile.id == profile_id).first()

    if not profile:
        return JSONResponse(
            status_code=404, content={"status": "error", "message": "Profile not found"}
        )
    db.delete(profile)
    db.commit()

    return 

@app.get("/")
def root():
    return {"message": "Name Profiler API", "version": "1.0.0"}