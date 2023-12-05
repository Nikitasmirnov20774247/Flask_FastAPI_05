import logging
from pathlib import Path
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from models import Base, User
from typing import Annotated
import uvicorn


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
db_path = Path(Path.cwd(), 'ds5.db')


app = FastAPI()
templates = Jinja2Templates(directory='templates')


class ValUser(BaseModel):
    name: str
    email: str
    password: str


def get_base():
    engine_ = create_engine(f'sqlite:///{db_path}', echo=True)
    session_ = Session(engine_)

    if not db_path.is_file():
        Base.metadata.create_all(engine_)
        user = User(name='user1', email='test1000@gmail.com', password='12345678')
        session_.add(user)
        session_.commit()
        
    return engine_, session_


engine, session = get_base()


@app.get('/users')
async def get_users(request: Request):
    users = session.query(User).all()
    return templates.TemplateResponse('index.html', {'request': request, 'users': users})


@app.get('/users/{id}')
async def get_user(request: Request, id: int):
    user = session.query(User).filter_by(id=id).first()
    if user:
        return templates.TemplateResponse('user.html', {'request': request, 'user': user})
    else:
        raise HTTPException(status_code=404)


@app.post('/users')
async def add_user(
    request: Request,
    name: Annotated[str, Form()],
    email: Annotated[str, Form()],
    password: Annotated[str, Form()],
):
    session.add(User(name=name, email=email, password=password))
    session.commit()

    return RedirectResponse(request.url_for('get_users'), status_code=303)


@app.post('/users/{id}')
async def edit_user_html(
    id: int,
    request: Request,
    name: Annotated[str, Form()],
    email: Annotated[str, Form()],
    password: Annotated[str, Form()],
):
    user = session.query(User).filter_by(id=id).first()
    
    if user:
        user.name = name
        user.email = email
        user.password = password
        session.commit()
        return RedirectResponse(request.url_for('get_users'), status_code=303)
    else:
        raise HTTPException(status_code=404)


@app.put('/users/{id}', response_model=ValUser)
async def edit_user_api( id: int, user_edit: ValUser):
    user = session.query(User).filter_by(id=id).first()
    
    if user:
        user.name = user_edit.name
        user.email = user_edit.email
        user.password = user_edit.password
        session.commit()
        return {'name': user.name,'email': user.email,'password': user.password}
    else:
        raise HTTPException(status_code=404)


@app.delete('/users/{id}')
async def delete_user_api(id: int):
    user = session.query(User).filter_by(id=id).first()
    if user:
        session.delete(user)
        session.commit()
        return {'msg': 'User deleted'}
    else:
        raise HTTPException(status_code=404)


@app.post('/users/{id}/del')
async def delete_user_html(id: int, request: Request):
    user = session.query(User).filter_by(id=id).first()
    if user:
        session.delete(user)
        session.commit()
        return RedirectResponse(request.url_for('get_users'), status_code=303)
    else:
        raise HTTPException(status_code=404)


if __name__ == '__main__':
    uvicorn.run("app:app", host='localhost', port=8000, reload=True)