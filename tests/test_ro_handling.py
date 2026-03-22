import unittest
from unittest.mock import patch, mock_open
import os
import errno
from fastapi import HTTPException
from api.main import _write_json, handle_save_error

class TestVercelReadOnly(unittest.TestCase):
    def test_write_json_ro_error(self):
        """Test that _write_json correctly identifies EROFS and raises PermissionError."""
        with patch("builtins.open", side_effect=OSError(errno.EROFS, "Read-only file system")):
            with self.assertRaises(PermissionError) as cm:
                _write_json("test.json", {"data": 1})
            self.assertIn("Read-only file system", str(cm.exception))

    def test_handle_save_error_ro(self):
        """Test that handle_save_error converts PermissingError (RO) to 501 HTTPException."""
        ro_error = PermissionError("Read-only file system: test.json")
        with self.assertRaises(HTTPException) as cm:
            handle_save_error(ro_error)
        self.assertEqual(cm.exception.status_code, 501)
        self.assertIn("Filesystem is read-only", cm.exception.detail)

    def test_handle_save_error_other(self):
        """Test that handle_save_error converts other errors to 500 HTTPException."""
        other_error = Exception("Some random error")
        with self.assertRaises(HTTPException) as cm:
            handle_save_error(other_error)
        self.assertEqual(cm.exception.status_code, 500)
        self.assertIn("Save failed", cm.exception.detail)

if __name__ == "__main__":
    unittest.main()
