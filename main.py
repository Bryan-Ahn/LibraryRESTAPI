from fastapi import FastAPI
import databases
import sqlalchemy
from pydantic import BaseModel, Field
from typing import List
import uuid

### Postgres Database ###
DATABASE_URL = "postgresql://postgres:root1234@127.0.0.1:5432/library"
database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

### Create table schema ###
books = sqlalchemy.Table(
    "db_books",
    metadata,
    sqlalchemy.Column("book_id", sqlalchemy.String, primary_key=True),
    sqlalchemy.Column("bookname", sqlalchemy.String),
    sqlalchemy.Column("author", sqlalchemy.String),
    sqlalchemy.Column("status", sqlalchemy.CHAR),
)

### create db engine ###
engine = sqlalchemy.create_engine(
    DATABASE_URL
)
metadata.create_all(engine)

### Models ###
class BookList(BaseModel):
    book_id : str
    bookname : str
    author : str
    status : str

class BookEntry(BaseModel): #model for add new books
    bookname : str = Field(..., example="bookname_ex")
    author : str = Field(..., example="author_ex")

class BookUpdate(BaseModel): #model for update the book's information
    book_id : str = Field(..., example="bookid_ex")
    bookname : str = Field(..., example="bookname_ex")
    author : str = Field(..., example="author_ex")
    status : str = Field(..., example="1")

class BookDelete(BaseModel): #model for delete the book
    book_id: str = Field(..., example="bookid_ex")

class BookBorrow(BaseModel): #model for borrowing book using book identifier
    book_id: str = Field(..., example="bookid_ex")
    status: str = Field(..., example="0") #status value "0" means book is returned

class BookReturn(BaseModel): #model for returning book using book identifier
    book_id: str = Field(..., example="bookid_ex")
    status: str = Field(..., example="1") #status value "1" means book is returned

app = FastAPI()

#db startup event
@app.on_event("startup")
async def startup():
    await database.connect()

#db shutdown event
@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

#print the entire book list
@app.get("/allbooks", response_model=List[BookList])
async def find_all_books():
    query = books.select()
    return await database.fetch_all(query)

#register new book on database
@app.post("/registerbook", response_model=BookList)
async def register_book(book: BookEntry):
    #generate GUID for the book by using uuid
    gID = str(uuid.uuid1())
    #initial value of status will be "1", which means book is not borrowed yet
    query = books.insert().values(
        book_id = gID,
        bookname = book.bookname,
        author = book.author,
        status = "1"
    )

    await database.execute(query)
    return {
        "book_id" : gID,
        **book.dict(),
        "status" : "1"
    }

#search the list of books by using the name of book
@app.get("/searchbyname/{bookname}", response_model=List[BookList])
async def find_book_by_name(bookname: str):
    query = books.select().where(books.c.bookname == bookname)
    return await database.fetch_all(query)

#search the book by using the book identifier
@app.get("/searchbyid/{book_id}", response_model=BookList)
async def find_book_by_id(book_id: str):
    query = books.select().where(books.c.book_id == book_id)
    return await database.fetch_one(query)

#search the list of books by using author's name
@app.get("/serarchbyauthor/{author}", response_model=List[BookList])
async def find_book_by_author(author: str):
    query = books.select().where(books.c.author == author)
    return await database.fetch_all(query)

#borrowing book by using the book identifier (to distinguish specific book)
@app.put("/borrowbook/{book_id}", response_model=BookBorrow)
async def borrow_book(book: BookBorrow):
    query = books.update().where(books.c.book_id == book.book_id).values(
        status="0",
    )
    await database.execute(query)
    return await find_book_by_id(book.book_id)

#returning book by using the book identifier (to distinguish specific book)
@app.put("/returnbook/{book_id}", response_model=BookReturn)
async def borrow_book(book: BookReturn):
    query = books.update().where(books.c.book_id == book.book_id).values(
        status="1",
    )
    await database.execute(query)
    return await find_book_by_id(book.book_id)

#update the information of book by using the book identifier (to distinguish specific book)
@app.put("/updatebook/{book_id}", response_model=BookList)
async def update_book(book: BookUpdate):
    query = books.update().where(books.c.book_id == book.book_id).values(
        bookname = book.bookname,
        author = book.author,
        status = book.status,
    )
    await database.execute(query)
    return await find_book_by_id(book.book_id)

#delete the book by using the book identifier
@app.delete("/deletebook/{book_id}")
async def delete_book(book: BookDelete):
    query = books.delete().where(books.c.book_id == book.book_id)
    await database.execute(query)
    return {
        "status" : True,
        "message" : "This book has been deleted successfully from the library database."
    }