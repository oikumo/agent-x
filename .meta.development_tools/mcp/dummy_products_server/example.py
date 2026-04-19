#!/usr/bin/env python3
"""Example usage of the Products MCP Server."""

from server import (
    add_product,
    get_products,
    get_product_by_sku,
    update_product,
    delete_product,
)


def main():
    """Demonstrate product management operations."""
    print("=" * 60)
    print("MCP Products Server - Example Usage")
    print("=" * 60)

    # Add products
    print("\n1. Adding products...")
    print(add_product("laptop-pro", 1200.0, 5))
    print(add_product("teclado-mecanico", 89.0, 10))
    print(add_product("mouse-wireless", 29.99, 25))

    # List all products
    print("\n2. Listing all products:")
    print(get_products())

    # Get specific product
    print("\n3. Getting product by SKU:")
    print(get_product_by_sku("laptop-pro"))

    # Update product
    print("\n4. Updating product:")
    print(update_product("laptop-pro", 1100.0, 3))
    print(get_product_by_sku("laptop-pro"))

    # Try to add duplicate
    print("\n5. Attempting to add duplicate:")
    print(add_product("laptop-pro", 999.0, 1))

    # Validate price
    print("\n6. Validating negative price:")
    print(add_product("invalid-product", -10.0, 5))

    # Delete product
    print("\n7. Deleting product:")
    print(delete_product("mouse-wireless"))
    print(get_products())

    # Try to get deleted product
    print("\n8. Getting deleted product:")
    print(get_product_by_sku("mouse-wireless"))

    print("\n" + "=" * 60)
    print("Example completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
