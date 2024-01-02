from contextlib import asynccontextmanager
from datetime import date
from typing import Annotated

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastui import FastUI, AnyComponent, prebuilt_html, components as c
from fastui.components.display import DisplayMode, DisplayLookup
from fastui.events import GoToEvent, BackEvent
from fastui.forms import FormResponse, fastui_form
from pydantic import BaseModel, Field
from db import User, engine
from sqlmodel import Session, select


@asynccontextmanager
async def lifespan(app: FastAPI):
    # define some users
    users = [
        User(id=1, name='John', dob=date(1990, 1, 1)),
        User(id=2, name='Jack', dob=date(1991, 1, 1)),
        User(id=3, name='Jill', dob=date(1992, 1, 1)),
        User(id=4, name='Jane', dob=date(1993, 1, 1)),
    ]
    with Session(engine) as session:
        for user in users:
            db_user = session.get(User, user.id)
            if db_user is not None:
                continue
            session.add(user)
        session.commit()
    yield


app = FastAPI(lifespan=lifespan)


class UserForm(BaseModel):
    name: str
    dob: date

class DeleteUserForm(BaseModel):
    confirm: bool


@app.get('/api/user/add/', response_model=FastUI, response_model_exclude_none=True)
def add_user():
    return [
        c.Page( 
            components=[
                c.Heading(text='Add User', level=2),
                c.Paragraph(text='Add a user to the system'),
                c.ModelForm[UserForm](
                    submit_url='/api/user/add/'
                ),
            ]
        )
    ]   

@app.post('/api/user/add/')
async def add_user(form: Annotated[UserForm, fastui_form(UserForm)]) -> FormResponse:
    with Session(engine) as session:
        user = User(**form.model_dump())
        session.add(user)
        session.commit()

    return FormResponse(event=GoToEvent(url='/'))

@app.get("/api/", response_model=FastUI, response_model_exclude_none=True)
def users_table() -> list[AnyComponent]:
    
    with Session(engine) as session:
        users = session.exec(select(User)).all()

    return [
        c.Page(  # Page provides a basic container for components
            components=[
                c.Heading(text='Users', level=2),  # renders `<h2>Users</h2>`
                c.Table[User](  # c.Table is a generic component parameterized with the model used for rows
                    data=users,
                    # define two columns for the table
                    columns=[
                        # the first is the users, name rendered as a link to their profile
                        DisplayLookup(field='name', on_click=GoToEvent(url='/user/{id}/')),
                        # the second is the date of birth, rendered as a date
                        DisplayLookup(field='dob', mode=DisplayMode.date),
                    ],
                ),
                c.Div(components=[
                    c.Link(
                        components=[c.Button(text='Add User')],
                        on_click=GoToEvent(url='/user/add/'),
                    ),
                ])
            ]
        ),
    ]

@app.get("/api/user/{user_id}/", response_model=FastUI, response_model_exclude_none=True)
def user_profile(user_id: int) -> list[AnyComponent]:
    """
    User profile page, the frontend will fetch this when the user visits `/user/{id}/`.
    """
    with Session(engine) as session:
        user = session.get(User, user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        
    return [
        c.Page(
            components=[
                c.Heading(text=user.name, level=2),
                c.Link(components=[c.Text(text='Back')], on_click=BackEvent()),
                c.Details(data=user),
                c.Div(components=[
                    c.Heading(text="Delete User?", level=4),
                    c.ModelForm[DeleteUserForm](
                        submit_url=f'/api/user/{user_id}/delete/',
                        class_name="text-left"
                    )
                ], class_name="card p-4 col-4")
            ]
        ),
    ]

@app.post('/api/user/{user_id}/delete/')
async def delete_user(
    user_id: int, 
    form: Annotated[DeleteUserForm, fastui_form(DeleteUserForm)]
) -> FormResponse:
    # delete the users
    with Session(engine) as session:
        user = session.get(User, user_id)
        if user is not None:
            session.delete(user)
            session.commit()

    return FormResponse(event=GoToEvent(url='/'))


@app.get('/{path:path}')
async def html_landing() -> HTMLResponse:
    """Simple HTML page which serves the React app, comes last as it matches all paths."""
    return HTMLResponse(prebuilt_html(title='FastUI Demo'))