import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database.db import init_db, create_user

if __name__ == '__main__':
    init_db()
    username = input("Username: ").strip()
    password = input("Password: ").strip()
    role = input("Role [admin/user] (default: user): ").strip().lower() or 'user'

    if not username or not password:
        print("Tidak boleh kosong.")
        sys.exit(1)
    if role not in ('admin', 'user'):
        print("Role tidak valid. Pilih 'admin' atau 'user'.")
        sys.exit(1)

    success = create_user(username, password, role)
    print(f"✅ User '{username}' ({role}) berhasil!" if success else f"❌ Username '{username}' sudah ada.")