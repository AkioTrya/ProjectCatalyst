import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database.db import init_db, create_user

if __name__ == '__main__':
    init_db()
    username = input("Username: ").strip()
    password = input("Password: ").strip()
    if not username or not password:
        print("Tidak boleh kosong.")
        sys.exit(1)
    success = create_user(username, password)
    print(f"✅ User '{username}' berhasil!" if success else f"❌ Username '{username}' sudah ada.")