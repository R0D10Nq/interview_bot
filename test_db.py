"""Проверка подключения к БД"""
import asyncio
from pathlib import Path

# Проверка каталогов
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
BACKUP_DIR = PROJECT_ROOT / "backups"

print(f"Корень проекта: {PROJECT_ROOT}")
print(f"Каталог данных: {DATA_DIR}")
print(f"Каталог резервных копий: {BACKUP_DIR}")

# Создание каталогов
DATA_DIR.mkdir(exist_ok=True)
BACKUP_DIR.mkdir(exist_ok=True)

print("\n✅ Каталоги созданы!")

# Тестирование подключения к БД
from app.config import settings
from app.database.database import init_db

print(f"\n📊 URL БД: {settings.database_url}")


async def test():
    """Тестирование инициализации БД."""
    try:
        await init_db()
        print("✅ БД успешно инициализирована!")
    except Exception as e:
        print(f"❌ Ошибка: {e}")


if __name__ == "__main__":
    asyncio.run(test())