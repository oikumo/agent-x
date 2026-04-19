"""Products MCP Server with SQLite database management."""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("mcp-server-products")


class ProductDB:
    """SQLite database manager for products."""

    def __init__(self, db_path: str = None):
        """Initialize database connection.

        Args:
            db_path: Path to SQLite database file. Defaults to products.db in current directory.
        """
        if db_path is None:
            db_path = Path(__file__).parent / "products.db"
        self.db_path = str(db_path)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()

    def create_tables(self):
        """Create products table if not exists."""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sku TEXT UNIQUE NOT NULL,
                price REAL NOT NULL,
                stock INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

    def delete_all(self):
        """Delete all products (for testing)."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM products")
        self.conn.commit()


# Global database instance - initialized on module load
_db_instance: Optional[ProductDB] = None


def get_db() -> ProductDB:
    """Get or create the global database instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = ProductDB()
    return _db_instance


def set_db_instance(db: ProductDB):
    """Set the database instance (for testing)."""
    global _db_instance
    _db_instance = db


def get_product_by_sku(sku: str) -> str:
    """Query the price and stock of a product.

    Args:
        sku: The product identifier.

    Returns:
        Formatted string with product information or not found message.
    """
    db = get_db()
    cursor = db.conn.cursor()
    cursor.execute("SELECT sku, price, stock FROM products WHERE sku = ?", (sku,))
    row = cursor.fetchone()

    if not row:
        return f"Product '{sku}' not found"

    return f"SKU: {row['sku']} | Price: ${row['price']} | Stock: {row['stock']}"


def get_products() -> str:
    """List all SKUs available in the inventory.

    Returns:
        Comma-separated list of product SKUs.
    """
    db = get_db()
    cursor = db.conn.cursor()
    cursor.execute("SELECT sku FROM products ORDER BY sku")
    rows = cursor.fetchall()

    if not rows:
        return "SKUs:"

    skus = ", ".join(row["sku"] for row in rows)
    return f"SKUs: {skus}"


def add_product(sku: str, price: float, stock: int = 0) -> str:
    """Add a new product to the inventory.

    Args:
        sku: Product identifier (must be unique).
        price: Product price (must be non-negative).
        stock: Quantity in stock (default: 0).

    Returns:
        Confirmation message or error.
    """
    db = get_db()

    # Validate inputs
    sku = sku.strip()

    if price < 0:
        return "Error: Price cannot be negative"

    if stock < 0:
        return "Error: Stock cannot be negative"

    try:
        cursor = db.conn.cursor()
        cursor.execute(
            "INSERT INTO products (sku, price, stock, created_at) VALUES (?, ?, ?, ?)",
            (sku, price, stock, datetime.now()),
        )
        db.conn.commit()
        return f"Product '{sku}' added successfully (Price: ${price}, Stock: {stock})"
    except sqlite3.IntegrityError:
        return f"Error: Product '{sku}' already exists"


def update_product(sku: str, price: float, stock: int) -> str:
    """Update an existing product's price and stock.

    Args:
        sku: Product identifier.
        price: New price.
        stock: New stock quantity.

    Returns:
        Confirmation message or not found error.
    """
    db = get_db()
    cursor = db.conn.cursor()
    cursor.execute("SELECT sku FROM products WHERE sku = ?", (sku,))

    if not cursor.fetchone():
        return f"Product '{sku}' not found"

    cursor.execute(
        "UPDATE products SET price = ?, stock = ? WHERE sku = ?", (price, stock, sku)
    )
    db.conn.commit()
    return f"Product '{sku}' updated (Price: ${price}, Stock: {stock})"


def delete_product(sku: str) -> str:
    """Delete a product from the inventory.

    Args:
        sku: Product identifier.

    Returns:
        Confirmation message or not found error.
    """
    db = get_db()
    cursor = db.conn.cursor()
    cursor.execute("SELECT sku FROM products WHERE sku = ?", (sku,))

    if not cursor.fetchone():
        return f"Product '{sku}' not found"

    cursor.execute("DELETE FROM products WHERE sku = ?", (sku,))
    db.conn.commit()
    return f"Product '{sku}' deleted successfully"


@mcp.tool()
def get_products_tool() -> str:
    """MCP tool: Lists all SKUs available in the inventory."""
    return get_products()


@mcp.tool()
def get_product_by_sku_tool(sku: str) -> str:
    """MCP tool: Queries the price and stock of a product.

    Args:
        sku: The product identifier. Use it exactly as it appears in get_products.
    """
    return get_product_by_sku(sku)


@mcp.tool()
def add_product_tool(sku: str, price: float, stock: int = 0) -> str:
    """MCP tool: Add a new product to the inventory.

    Args:
        sku: Product identifier (must be unique).
        price: Product price (must be non-negative).
        stock: Quantity in stock (default: 0).
    """
    return add_product(sku, price, stock)


@mcp.tool()
def update_product_tool(sku: str, price: float, stock: int) -> str:
    """MCP tool: Update an existing product's price and stock.

    Args:
        sku: Product identifier.
        price: New price.
        stock: New stock quantity.
    """
    return update_product(sku, price, stock)


@mcp.tool()
def delete_product_tool(sku: str) -> str:
    """MCP tool: Delete a product from the inventory.

    Args:
        sku: Product identifier.
    """
    return delete_product(sku)


if __name__ == "__main__":
    mcp.run(transport="stdio")
