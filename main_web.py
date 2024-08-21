import os

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from strawberry import Schema
from strawberry.fastapi import GraphQLRouter

from src.database_service import DatabaseService
from src.schema import Query, Mutation

load_dotenv()

app = FastAPI()
database_url = os.getenv("DATABASE_URL")
database_service = DatabaseService(database_url=database_url)
schema = Schema(query=Query, mutation=Mutation)


async def get_context(db: Session = Depends(database_service.get_db)):
    return {"db": db}


graphql_app = GraphQLRouter(schema, context_getter=get_context)
app.include_router(graphql_app, prefix="/graphql")


@app.get("/")
def read_root():
    return {"Hello": "World"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8081)
