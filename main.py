import aiosqlite
from fastapi import FastAPI, Response, status
from pydantic import BaseModel

app = FastAPI()

@app.on_event("startup")
async def startup():
    app.db_connection = await aiosqlite.connect('chinook.db')

@app.on_event("shutdown")
async def shutdown():
    await app.db_connection.close()

@app.get("/tracks")
async def get_tracks(page: int = 0, per_page: int = 10):
    app.db_connection.row_factory = aiosqlite.Row
    cursor = await app.db_connection.execute("SELECT * FROM tracks ORDER BY TrackId LIMIT :per_page OFFSET :per_page*:page",
        {'page': page, 'per_page': per_page})
    tracks = await cursor.fetchall()
    return tracks

@app.get("/tracks/composers")
async def get_tracks_by_composer(response: Response, composer_name: str):
    app.db_connection.row_factory = lambda cursor, x: x[0]
    cursor = await app.db_connection.execute("SELECT Name FROM tracks WHERE Composer = :composer_name ORDER BY Name",
        {'composer_name': composer_name})
    tracks = await cursor.fetchall()

    if len(tracks) == 0:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"detail":{"error":"No tracks by this composer."}}
    return tracks

class Album(BaseModel):
    title : str
    artist_id: int

@app.post("/albums")
async def post_album(response: Response, album: Album):
    cursor = await app.db_connection.execute("SELECT ArtistId FROM artists WHERE ArtistId = :artist_id",
        {'artist_id': album.artist_id})
    result = await cursor.fetchone()
    
    if result is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"detail":{"error":"Unknown artist."}}

    cursor = await app.db_connection.execute("INSERT INTO albums (Title, ArtistId) VALUES (:title, :artist_id)",
        {'artist_id': album.artist_id, 'title': album.title})
    await app.db_connection.commit()
    response.status_code = status.HTTP_201_CREATED
    return {"AlbumId": cursor.lastrowid, "Title": album.title, "ArtistId": album.artist_id}


@app.get("/albums/{album_id}")
async def get_album(album_id: int):
    app.db_connection.row_factory = aiosqlite.Row
    cursor = await app.db_connection.execute("SELECT * FROM albums WHERE AlbumId = :album_id",
        {'album_id': album_id})
    album = await cursor.fetchone()
    return album

class Customer(BaseModel):
    company: str = None
    address: str = None
    city: str = None
    state: str = None
    country: str = None
    postalcode: str = None
    fax: str = None

@app.put("/customers/{customer_id}")
async def put_customer(response: Response, customer_id: int, customer: Customer):
    cursor = await app.db_connection.execute("SELECT CustomerId FROM customers WHERE CustomerId = :customer_id",
        {"customer_id": customer_id})
    result = await cursor.fetchone()
    if result is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"detail": {"error": "Customer with that id does not exist."}}

    customer = {k: v for k, v in customer.dict().items() if v is not None}
    for key, value in customer.items():
        cursor = await app.db_connection.execute("UPDATE customers SET " + f"{key}" +" = :value WHERE CustomerId = :customer_id",
        {"customer_id": customer_id, "value": value})
        await app.db_connection.commit()

    app.db_connection.row_factory = aiosqlite.Row
    cursor = await app.db_connection.execute("SELECT * FROM customers WHERE CustomerId = :customer_id",
        {"customer_id": customer_id})
    customer = await cursor.fetchone()
    return customer

@app.get("/sales")
async def get_sales_statistics(response: Response, category: str):
    if category == "customers":
        app.db_connection.row_factory = aiosqlite.Row
        cursor = await app.db_connection.execute("SELECT invoices.CustomerId, Email, Phone, ROUND(SUM(Total), 2) AS Sum FROM invoices JOIN customers on invoices.CustomerId = customers.CustomerId GROUP BY invoices.CustomerId ORDER BY Sum DESC, invoices.CustomerId")
        sales = await cursor.fetchall()
        return sales

    elif category == "genres":
        app.db_connection.row_factory = aiosqlite.Row
        cursor = await app.db_connection.execute("SELECT genres.Name, SUM(Quantity) AS Sum FROM invoice_items JOIN tracks ON invoice_items.TrackId = tracks.TrackId JOIN genres ON tracks.GenreId = genres.GenreId GROUP BY tracks.GenreId ORDER BY Sum DESC, genres.Name")
        sales = await cursor.fetchall()
        return sales
    else:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"detail": {"error": "Wrong category name."}}