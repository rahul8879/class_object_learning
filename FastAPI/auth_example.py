from fastapi import FastAPI, Path, Query, HTTPException, Depends, Request
from fastapi.routing import APIRouter
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List

# Main entry point for running the application


def main():
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)


# Create an instance of FastAPI
app = FastAPI()

# Add CORS middleware
origins = ["*"]
app.add_middleware(CORSMiddleware, allow_origins=origins,
                   allow_methods=["*"], allow_headers=["*"])

# Custom middleware for logging requests


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        print(f"Request URL: {request.url}")
        response = await call_next(request)
        return response


app.add_middleware(LoggingMiddleware)

# Dependency function to validate API keys


def validate_api_key(api_key: str = Query(..., description="API key for authentication")):
    if api_key != "secure-api-key":
        raise HTTPException(status_code=403, detail="Invalid API key")

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

# Grouped routes using routers
router = APIRouter(prefix="/accounts", tags=["Accounts"])


@router.post("/", response_model=AccountResponse, dependencies=[Depends(validate_api_key)])
def create_account(account: Account):
    """
    Create a new bank account and store it in the database.
    """
    if account.account_number in accounts_db:
        raise HTTPException(status_code=400, detail="Account already exists")
    accounts_db[account.account_number] = account
    return {"account_number": account.account_number, "message": "Account successfully created!"}


@router.get("/{account_number}", response_model=Account, dependencies=[Depends(validate_api_key)])
def read_account(account_number: str = Path(..., description="The unique account number to retrieve")):
    """
    Retrieve account details by account number.
    """
    if account_number not in accounts_db:
        raise HTTPException(status_code=404, detail="Account not found")
    return accounts_db[account_number]


@router.put("/{account_number}", response_model=AccountResponse, dependencies=[Depends(validate_api_key)])
def update_account(account_number: str, account: Account):
    """
    Update an existing bank account by its account number.
    """
    if account_number not in accounts_db:
        raise HTTPException(status_code=404, detail="Account not found")
    accounts_db[account_number] = account
    return {"account_number": account.account_number, "message": "Account successfully updated!"}


@router.delete("/{account_number}", response_model=dict, dependencies=[Depends(validate_api_key)])
def delete_account(account_number: str):
    """
    Delete a bank account by its account number.
    """
    if account_number not in accounts_db:
        raise HTTPException(status_code=404, detail="Account not found")
    del accounts_db[account_number]
    return {"message": "Account successfully deleted!"}


@router.get("/search/", dependencies=[Depends(validate_api_key)])
def search_accounts(
    account_holder: Optional[str] = Query(
        None, description="Name of the account holder to search"),
    min_balance: Optional[float] = Query(
        None, description="Minimum balance to filter accounts")
):
    """
    Search accounts based on account holder name and/or minimum balance.
    """
    results = [
        account for account in accounts_db.values()
        if (not account_holder or account.account_holder == account_holder) and
           (min_balance is None or account.balance >= min_balance)
    ]
    return {"results": results}

# Error handling for custom exceptions


class InsufficientFundsException(Exception):
    def __init__(self, message: str):
        self.message = message


@app.exception_handler(InsufficientFundsException)
def insufficient_funds_handler(request: Request, exc: InsufficientFundsException):
    return JSONResponse(status_code=400, content={"detail": exc.message})


# Adding routes to the main app
app.include_router(router)

if __name__ == "__main__":
    main()
