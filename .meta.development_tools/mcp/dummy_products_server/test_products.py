"""Test suite for Products MCP Server with SQLite database management."""

import os
import tempfile
from pathlib import Path

import pytest

from server import (
    ProductDB,
    get_db,
    set_db_instance,
    get_products,
    get_product_by_sku,
    add_product,
    update_product,
    delete_product,
)


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test_products.db"
    db = ProductDB(str(db_path))
    # Set as global instance for testing
    set_db_instance(db)
    yield db
    # Cleanup
    if db_path.exists():
        db_path.unlink()
    os.rmdir(temp_dir)


@pytest.fixture
def seeded_db(temp_db):
    """Database with sample products."""
    add_product("laptop-pro", 1200.0, 5)
    add_product("teclado-mecanico", 89.0, 0)
    yield temp_db
    # Cleanup seeded data
    temp_db.delete_all()


class TestProductDB:
    """Test ProductDB CRUD operations."""

    def test_create_tables_creates_products_table(self, temp_db):
        """Should create products table with correct schema."""
        cursor = temp_db.conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='products'"
        )
        assert cursor.fetchone() is not None

    def test_create_tables_creates_correct_schema(self, temp_db):
        """Should create table with sku, price, stock columns."""
        cursor = temp_db.conn.cursor()
        cursor.execute("PRAGMA table_info(products)")
        columns = {row[1] for row in cursor.fetchall()}
        # id is also created as primary key
        assert "sku" in columns
        assert "price" in columns
        assert "stock" in columns
        assert "created_at" in columns

    def test_add_product_inserts_new_product(self, temp_db):
        """Should insert a new product and return success."""
        result = add_product("test-product", 99.99, 10)
        assert "added" in result.lower()

        cursor = temp_db.conn.cursor()
        cursor.execute(
            "SELECT sku, price, stock FROM products WHERE sku = 'test-product'"
        )
        row = cursor.fetchone()
        assert row is not None
        assert row["sku"] == "test-product"
        assert row["price"] == 99.99
        assert row["stock"] == 10

    def test_add_product_handles_duplicate_sku(self, temp_db):
        """Should return error message for duplicate SKU."""
        add_product("duplicate", 10.0, 1)
        result = add_product("duplicate", 20.0, 2)
        assert "already exists" in result.lower()

    def test_get_product_by_sku_returns_product(self, temp_db):
        """Should return product details for valid SKU."""
        add_product("existing", 50.0, 3)
        result = get_product_by_sku("existing")
        assert "existing" in result
        assert "50.0" in result
        assert "3" in result

    def test_get_product_by_sku_returns_not_found(self, temp_db):
        """Should return not found message for invalid SKU."""
        result = get_product_by_sku("nonexistent")
        assert "not found" in result.lower()

    def test_update_product_modifies_existing(self, temp_db):
        """Should update price and stock for existing product."""
        add_product("updatable", 100.0, 5)
        result = update_product("updatable", 150.0, 10)
        assert "updated" in result.lower()

        cursor = temp_db.conn.cursor()
        cursor.execute("SELECT price, stock FROM products WHERE sku = 'updatable'")
        row = cursor.fetchone()
        assert row is not None
        assert row["price"] == 150.0
        assert row["stock"] == 10

    def test_update_product_handles_nonexistent(self, temp_db):
        """Should return not found for updating nonexistent product."""
        result = update_product("nonexistent", 100.0, 5)
        assert "not found" in result.lower()

    def test_delete_product_removes_product(self, temp_db):
        """Should delete product from database."""
        add_product("deletable", 25.0, 2)
        result = delete_product("deletable")
        assert "deleted" in result.lower()

        cursor = temp_db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM products WHERE sku = 'deletable'")
        assert cursor.fetchone()[0] == 0

    def test_delete_product_handles_nonexistent(self, temp_db):
        """Should return not found for deleting nonexistent product."""
        result = delete_product("nonexistent")
        assert "not found" in result.lower()


class TestGetProducts:
    """Test get_products tool."""

    def test_get_products_returns_all_skus(self, seeded_db):
        """Should return comma-separated list of all SKUs."""
        result = get_products()
        assert "laptop-pro" in result
        assert "teclado-mecanico" in result

    def test_get_products_empty_inventory(self, temp_db):
        """Should handle empty inventory gracefully."""
        result = get_products()
        assert "SKUs:" in result
        assert result.strip() == "SKUs:"


class TestGetProductBySku:
    """Test get_product_by_sku tool."""

    def test_returns_formatted_product_info(self, temp_db):
        """Should return formatted product information."""
        add_product("test-sku", 199.99, 7)
        result = get_product_by_sku("test-sku")
        assert "SKU:" in result
        assert "test-sku" in result
        assert "199.99" in result
        assert "7" in result

    def test_case_sensitive_sku(self, temp_db):
        """Should be case-sensitive for SKU lookup."""
        add_product("Test-SKU", 10.0, 1)
        result_lower = get_product_by_sku("test-sku")
        result_upper = get_product_by_sku("Test-SKU")
        assert "not found" in result_lower.lower()
        assert "Test-SKU" in result_upper


class TestAddProduct:
    """Test add_product tool."""

    def test_add_product_success(self, temp_db):
        """Should add product and return confirmation."""
        result = add_product("new-product", 299.99, 15)
        assert "added" in result.lower()
        assert "new-product" in result

    def test_add_product_with_zero_stock(self, temp_db):
        """Should allow adding product with zero stock."""
        result = add_product("zero-stock", 50.0, 0)
        assert "added" in result.lower()

    def test_add_product_validates_price(self, temp_db):
        """Should handle negative price."""
        result = add_product("negative-price", -10.0, 5)
        assert "error" in result.lower()

    def test_add_product_trims_sku(self, temp_db):
        """Should trim whitespace from SKU."""
        result = add_product("  trimmed-sku  ", 10.0, 1)
        assert "trimmed-sku" in result


class TestUpdateProduct:
    """Test update_product tool."""

    def test_update_product_success(self, temp_db):
        """Should update product and return confirmation."""
        add_product("update-me", 100.0, 5)
        result = update_product("update-me", 200.0, 10)
        assert "updated" in result.lower()

    def test_update_partial_fields(self, temp_db):
        """Should update both price and stock."""
        add_product("partial", 100.0, 5)
        result = update_product("partial", 150.0, 20)
        assert "150.0" in result or "20" in result


class TestDeleteProduct:
    """Test delete_product tool."""

    def test_delete_product_success(self, temp_db):
        """Should delete product and return confirmation."""
        add_product("to-delete", 50.0, 3)
        result = delete_product("to-delete")
        assert "deleted" in result.lower()

    def test_delete_product_cannot_recover(self, temp_db):
        """Should permanently remove product."""
        add_product("gone", 30.0, 2)
        delete_product("gone")
        result = get_product_by_sku("gone")
        assert "not found" in result.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
