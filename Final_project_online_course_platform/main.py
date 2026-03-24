from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field
from typing import Optional

app = FastAPI()

# ================= DATABASE =================
courses = []
wishlist = []
enrollments = []

# ================= MODELS =================
class Course(BaseModel):
    title: str = Field(..., min_length=3)
    price: float = Field(..., gt=0)
    category: str = Field(..., min_length=3)
    duration: int = Field(..., gt=0)
    instructor: str = Field(..., min_length=3)
    students: int = 0

class CourseUpdate(BaseModel):
    title: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None
    duration: Optional[int] = None
    instructor: Optional[str] = None

# ================= HELPERS =================
def find_course(course_id: int):
    for course in courses:
        if course["id"] == course_id:
            return course
    return None

def filter_courses(category=None, max_price=None):
    result = courses
    if category is not None:
        result = [c for c in result if c["category"].lower() == category.lower()]
    if max_price is not None:
        result = [c for c in result if c["price"] <= max_price]
    return result

# ================= DAY 1 =================
@app.get("/")
def home():
    return {"message": "Online Course Platform API"}

@app.get("/courses")
def get_courses():
    return courses

@app.get("/courses/count")
def course_count():
    return {"total_courses": len(courses)}

@app.get("/courses/summary")
def summary():
    if not courses:
        return {"message": "No courses available"}
    avg_price = sum(c["price"] for c in courses) / len(courses)
    total_students = sum(c["students"] for c in courses)
    return {"average_price": avg_price, "total_students": total_students}

# ================= DAY 3 =================
@app.get("/courses/filter")
def filter_api(category: Optional[str] = Query(None), max_price: Optional[float] = Query(None)):
    return filter_courses(category, max_price)

# ================= DAY 6 (IMPORTANT ORDER) =================

# ✅ SEARCH (must come before /courses/{course_id})
@app.get("/search-courses")
def search_courses(keyword: str = Query(...)):
    result = [
        c for c in courses
        if keyword.lower() in c["title"].lower()
        or keyword.lower() in c["category"].lower()
        or keyword.lower() in c["instructor"].lower()
    ]
    return result
# ✅ SORT
@app.get("/courses/sort")
def sort_courses(sort_by: str = "price", order: str = "asc"):
    if sort_by not in ["price", "duration", "students"]:
        raise HTTPException(status_code=400, detail="Invalid sort field")
    reverse = True if order == "desc" else False
    return sorted(courses, key=lambda x: x[sort_by], reverse=reverse)

# ✅ PAGINATION
@app.get("/courses/page")
def paginate(page: int = 1, limit: int = 5):
    total = len(courses)
    total_pages = (total + limit - 1) // limit
    start = (page - 1) * limit
    end = start + limit
    return {"page": page, "total_pages": total_pages, "data": courses[start:end]}

# ✅ BROWSE (combined)
@app.get("/courses/browse")
def browse(keyword: Optional[str] = None, sort_by: Optional[str] = None, order: str = "asc", page: int = 1, limit: int = 5):
    result = courses

    if keyword:
        result = [
            c for c in result
            if keyword.lower() in c["title"].lower()
            or keyword.lower() in c["category"].lower()
        ]

    if sort_by:
        reverse = True if order == "desc" else False
        result = sorted(result, key=lambda x: x[sort_by], reverse=reverse)

    total = len(result)
    total_pages = (total + limit - 1) // limit
    start = (page - 1) * limit
    end = start + limit

    return {"page": page, "total_pages": total_pages, "data": result[start:end]}

# ================= DAY 2 =================
@app.post("/courses", status_code=status.HTTP_201_CREATED)
def add_course(course: Course):
    for c in courses:
        if c["title"].lower() == course.title.lower():
            raise HTTPException(status_code=400, detail="Course already exists")

    new_course = course.dict()
    new_course["id"] = len(courses) + 1
    courses.append(new_course)

    return {"message": "Course added successfully", "data": new_course}

# ================= DAY 5 =================
@app.post("/wishlist/add")
def add_to_wishlist(course_id: int):
    course = find_course(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    wishlist.append(course)
    return {"message": "Added to wishlist"}

@app.post("/enroll")
def enroll(course_id: int):
    course = find_course(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    course["students"] += 1
    enrollments.append(course)
    return {"message": "Enrolled successfully"}

@app.post("/complete-course")
def complete_course(course_id: int):
    course = find_course(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return {"message": f"{course['title']} completed"}

# ================= DAY 4 (KEEP LAST) =================
@app.put("/courses/id/{course_id}")
def update_course(course_id: int, updated: CourseUpdate):
    course = find_course(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    update_data = updated.dict(exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided")

    for key, value in update_data.items():
        course[key] = value

    return {"message": "Course updated successfully", "data": course}

@app.delete("/courses/id/{course_id}")
def delete_course(course_id: int):
    course = find_course(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if course["students"] > 0:
        raise HTTPException(status_code=400, detail="Cannot delete enrolled course")

    courses.remove(course)
    return {"message": "Course deleted successfully"}

@app.get("/courses/id/{course_id}")
def get_course(course_id: int):
    course = find_course(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@app.on_event("startup")
def show_routes():
    print("\n--- ROUTES LIST ---")
    for route in app.routes:
        print(route.path)
    print("-------------------\n")


   