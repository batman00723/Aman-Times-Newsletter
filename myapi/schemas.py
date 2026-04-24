from ninja import Schema

class UserIn(Schema):
    id: int
    username: str
    email: str = Field(
            ..., 
            pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
            description="Must be a valid email format"
        )

class UserOut(Schema):
    id: int
    username: str
    email: str = Field(
            ..., 
            pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
            description="Must be a valid email format"
        )