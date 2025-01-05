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


class Account(BaseModel):
    account_number: str = Field(..., example="1234567890",
                                description="The unique account number")
    account_holder: str = Field(..., example="John Doe",
                                description="The name of the account holder")
    balance: float = Field(..., gt=0, example=1000.50,
                           description="The initial balance of the account")
    account_type: str = Field(..., example="Savings",
                              description="Type of the account (e.g., Savings, Current)")

# Define a Pydantic model for response validation


class AccountResponse(BaseModel):
    account_number: str
    message: str


# In-memory storage for accounts
accounts_db = {}

# Route to create a new bank account using POST


@app.post("/accounts/", response_model=AccountResponse)
def create_account(account: Account):
    """
    Create a new bank account and store it in the database.
    """
    if account.account_number in accounts_db:
        raise HTTPException(status_code=400, detail="Account already exists")
    accounts_db[account.account_number] = account
    return {"account_number": account.account_number, "message": "Account successfully created!"}

# Route to retrieve account details using GET


@app.get("/accounts/{account_number}", response_model=Account)
def read_account(account_number: str = Path(..., description="The unique account number to retrieve")):
    """
    Retrieve account details by account number.
    """
    if account_number not in accounts_db:
        raise HTTPException(status_code=404, detail="Account not found")
    return accounts_db[account_number]

# Route to update account details using PUT


@app.put("/accounts/{account_number}", response_model=AccountResponse)
def update_account(account_number: str, account: Account):
    """
    Update an existing bank account by its account number.
    """
    if account_number not in accounts_db:
        raise HTTPException(status_code=404, detail="Account not found")
    accounts_db[account_number] = account
    return {"account_number": account.account_number, "message": "Account successfully updated!"}

# Route to delete a bank account using DELETE


@app.delete("/accounts/{account_number}", response_model=dict)
def delete_account(account_number: str):
    """
    Delete a bank account by its account number.
    """
    if account_number not in accounts_db:
        raise HTTPException(status_code=404, detail="Account not found")
    del accounts_db[account_number]
    return {"message": "Account successfully deleted!"}

# Route demonstrating query parameters for account search


@app.get("/search-accounts/")
def search_accounts(account_holder: Optional[str] = Query(None, description="Name of the account holder to search"), min_balance: Optional[float] = Query(None, gt=0, description="Minimum balance to filter accounts")):
    """
    Search accounts based on account holder name and/or minimum balance.
    """
    results = [account for account in accounts_db.values() if (not account_holder or account.account_holder ==
                                                               account_holder) and (not min_balance or account.balance >= min_balance)]
    return {"results": results}


if __name__ == "__main__":
    main()
