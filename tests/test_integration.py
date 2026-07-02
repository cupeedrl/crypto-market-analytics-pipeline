import unittest
import psycopg2
import os
from unittest import skipIf


class TestIntegration(unittest.TestCase):
    @skipIf(os.environ.get("CI") == "true", "Skip in CI - no database available")
    def test_postgres_connection(self):
        """Test kết nối PostgreSQL"""
        try:
            conn = psycopg2.connect(
                host="localhost",
                port="5433",
                database="crypto_ods",
                user="admin",
                password="admin123",
            )
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            conn.close()
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"PostgreSQL connection failed: {e}")

    @skipIf(os.environ.get("CI") == "true", "Skip in CI - no database available")
    def test_real_time_prices_table_exists(self):
        """Test bảng real_time_prices tồn tại"""
        conn = psycopg2.connect(
            host="localhost",
            port="5433",
            database="crypto_ods",
            user="admin",
            password="admin123",
        )
        cursor = conn.cursor()
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'real_time_prices'
            );
        """)
        exists = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        self.assertTrue(exists)


if __name__ == "__main__":
    unittest.main()
