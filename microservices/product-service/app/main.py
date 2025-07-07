from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Optional
import uuid
import uvicorn
import os
from datetime import datetime

app = FastAPI(title="Product Service", description="microservicio para gestión de productos", version="1.0.0")

# modelos de datos
class Product(BaseModel):
    id: str = None
    name: str
    description: str
    price: float
    category: str
    stock: int
    created_at: datetime = None
    updated_at: datetime = None

class ProductCreate(BaseModel):
    name: str
    description: str
    price: float
    category: str
    stock: int

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None
    stock: Optional[int] = None

# almacenamiento en memoria
products_db: Dict[str, Product] = {}

@app.get("/health")
async def health_check():
    """health check"""
    return {"status": "healthy", "service": "product-service"}

@app.post("/products", response_model=Product)
async def create_product(product_data: ProductCreate):
    """crear producto"""
    product_id = str(uuid.uuid4())
    now = datetime.now()
    product = Product(
        id=product_id,
        created_at=now,
        updated_at=now,
        **product_data.dict()
    )
    products_db[product_id] = product
    return product

@app.get("/products", response_model=List[Product])
async def search_products(
    name: Optional[str] = Query(None, description="buscar por nombre"),
    category: Optional[str] = Query(None, description="filtrar por categoría"),
    min_price: Optional[float] = Query(None, description="precio mínimo"),
    max_price: Optional[float] = Query(None, description="precio máximo"),
    limit: int = Query(10, description="número máximo de resultados")
):
    """buscar productos con filtros"""
    results = list(products_db.values())
    
    # aplicar filtros
    if name:
        results = [p for p in results if name.lower() in p.name.lower()]
    
    if category:
        results = [p for p in results if category.lower() == p.category.lower()]
    
    if min_price is not None:
        results = [p for p in results if p.price >= min_price]
    
    if max_price is not None:
        results = [p for p in results if p.price <= max_price]
    
    # limitar resultados
    return results[:limit]

@app.get("/products/{product_id}", response_model=Product)
async def get_product(product_id: str):
    """obtener producto específico"""
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    return products_db[product_id]

@app.put("/products/{product_id}", response_model=Product)
async def update_product(product_id: str, product_data: ProductUpdate):
    """actualizar producto"""
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product = products_db[product_id]
    update_data = product_data.dict(exclude_unset=True)
    
    # actualizar campos modificados
    for field, value in update_data.items():
        setattr(product, field, value)
    
    # actualizar timestamp
    product.updated_at = datetime.now()
    products_db[product_id] = product
    
    return product

@app.get("/products/category/{category}", response_model=List[Product])
async def get_products_by_category(category: str):
    """obtener productos por categoría"""
    results = [p for p in products_db.values() if p.category.lower() == category.lower()]
    return results

@app.get("/stats")
async def get_product_stats():
    """obtener estadísticas de productos"""
    total_products = len(products_db)
    total_stock = sum(p.stock for p in products_db.values())
    categories = list(set(p.category for p in products_db.values()))
    
    return {
        "total_products": total_products,
        "total_stock": total_stock,
        "categories": categories,
        "timestamp": datetime.now()
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port) 