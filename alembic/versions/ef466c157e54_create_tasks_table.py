"""create tasks table

Revision ID: ef466c157e54
Revises: 
Create Date: 2025-11-28 12:53:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ef466c157e54'
down_revision: str | None = None
branch_labels: str | tuple[str] | None = None
depends_on: str | tuple[str] | None = None


def upgrade() -> None:
    # This command executes the raw SQL to create the tasks table.
    op.execute("""
        CREATE TABLE tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL, 
            title TEXT NOT NULL,
            description TEXT,
            is_done BOOLEAN NOT NULL DEFAULT 0,
            UNIQUE(id, user_id) 
        );
    """)


def downgrade() -> None:
    # This command executes the raw SQL to drop the table, reversing the upgrade.
    op.drop_table('tasks')
