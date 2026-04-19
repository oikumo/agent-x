# MCP Products Server

A Model Context Protocol (MCP) server for managing product inventory with SQLite database persistence.

## Features

- **SQLite Database**: Products are stored in a local SQLite database (`products.db`)
- **Full CRUD Operations**: Create, Read, Update, Delete products
- **MCP Tools**: 5 exposed tools for product management
- **TDD Tested**: Comprehensive test suite with 22 passing tests

## MCP Tools

The server exposes the following tools:

### `get_products_tool()`
Lists all SKUs available in the inventory.

**Returns**: Comma-separated list of product SKUs

### `get_product_by_sku_tool(sku: str)`
Queries the price and stock of a specific product.

**Args**:
- `sku`: The product identifier

**Returns**: Formatted string with product information or not found message

### `add_product_tool(sku: str, price: float, stock: int = 0)`
Adds a new product to the inventory.

**Args**:
- `sku`: Product identifier (must be unique, trimmed of whitespace)
- `price`: Product price (must be non-negative)
- `stock`: Quantity in stock (default: 0)

**Returns**: Confirmation message or error

### `update_product_tool(sku: str, price: float, stock: int)`
Updates an existing product's price and stock.

**Args**:
- `sku`: Product identifier
- `price`: New price
- `stock`: New stock quantity

**Returns**: Confirmation message or not found error

### `delete_product_tool(sku: str)`
Deletes a product from the inventory.

**Args**:
- `sku`: Product identifier

**Returns**: Confirmation message or not found error

## Running the Server

### Run the server in stdio mode (required for Claude)

```bash
uv run server.py
```

## Testing

Run the test suite:

```bash
uv run pytest test_products.py -v
```

All 22 tests should pass.

## Database Schema

```sql
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku TEXT UNIQUE NOT NULL,
    price REAL NOT NULL,
    stock INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Connection Examples

### MCP Inspector

```bash
npx @modelcontextprotocol/inspector
```

Then connect to `http://localhost:8000/mcp` using Streamable HTTP transport.

### Claude Code Connection

Add to `.mcp.json` in your project root:

```json
{
  "mcpServers": {
    "products_server": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/products_server",
        "run",
        "server.py"
      ]
    }
  }
}
```

### Verify with cURL

```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
```

## Example Usage

```python
# Add products
add_product("laptop-pro", 1200.0, 5)
add_product("teclado-mecanico", 89.0, 10)

# List all products
print(get_products())  # SKUs: laptop-pro, teclado-mecanico

# Get specific product
print(get_product_by_sku("laptop-pro"))  
# SKU: laptop-pro | Price: $1200.0 | Stock: 5

# Update product
update_product("laptop-pro", 1100.0, 3)

# Delete product
delete_product("teclado-mecanico")
```
