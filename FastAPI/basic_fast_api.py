# Import necessary modules from FastAPI
from fastapi import FastAPI, Path, Query, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

# Main entry point for running the application


def main():
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)


# Create an instance of FastAPI
app = FastAPI()

# Define a Pydantic model for request body validation


class Item(BaseModel):
    name: str = Field(..., example="Apple", description="The name of the item")
    price: float = Field(..., gt=0, example=10.5,
                         description="The price of the item")
    description: Optional[str] = Field(
        None, example="A fresh apple", description="Description of the item")
    in_stock: bool = Field(..., example=True,
                           description="Availability of the item")

# Define a Pydantic model for response validation


class ItemResponse(BaseModel):
    id: int
    name: str
    message: str


# In-memory storage for items
items_db = {}

# Route to create an item using POST


@app.post("/items/", response_model=ItemResponse)
def create_item(item: Item):
    """
    Create a new item and store it in the database.
    """
    item_id = len(items_db) + 1
    items_db[item_id] = item
    return {"id": item_id, "name": item.name, "message": "Item successfully created!"}

# Route to retrieve an item using GET


@app.get("/items/{item_id}", response_model=Item)
def read_item(item_id: int = Path(..., gt=0, description="The ID of the item to retrieve")):
    """
    Retrieve an item by its ID.
    """
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    return items_db[item_id]

# Route to update an item using PUT


@app.put("/items/{item_id}", response_model=ItemResponse)
def update_item(item_id: int, item: Item):
    """
    Update an existing item by its ID.
    """
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    items_db[item_id] = item
    return {"id": item_id, "name": item.name, "message": "Item successfully updated!"}

# Route to delete an item using DELETE


@app.delete("/items/{item_id}", response_model=dict)
def delete_item(item_id: int):
    """
    Delete an item by its ID.
    """
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    del items_db[item_id]
    return {"message": "Item successfully deleted!"}

# Route demonstrating query parameters


@app.get("/search/")
def search_items(name: Optional[str] = Query(None, description="Name of the item to search"), max_price: Optional[float] = Query(None, gt=0, description="Maximum price of the item")):
    """
    Search items based on name and/or maximum price.
    """
    results = [item for item in items_db.values() if (
        not name or item.name == name) and (not max_price or item.price <= max_price)]
    return {"results": results}

# Custom validator example


@app.post("/validated-item/")
def create_validated_item(item: Item):
    """
    Create an item with additional validation logic.
    """
    if len(item.name) < 3:
        raise HTTPException(
            status_code=400, detail="Item name must be at least 3 characters long")
    return {"message": "Item passed custom validation and was created!"}


if __name__ == "__main__":
    main()
