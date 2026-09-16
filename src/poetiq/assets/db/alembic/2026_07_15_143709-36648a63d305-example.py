"""example

Revision ID: 36648a63d305
Revises:
Create Date: 2026-07-15 14:37:09.521278

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from pydantic_table.alembic import op as opp
from alembic_migrations.models import ExampleTable

# revision identifiers, used by Alembic.
revision: str = "36648a63d305"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

id = 42

def upgrade() -> None:
    """Upgrade schema."""
    opp.create_table(ExampleTable)
    data = ExampleTable(id=id, name="Alice", value=2.718)
    opp.insert(data)


def downgrade() -> None:
    """Downgrade schema."""
    opp.delete_where(ExampleTable, id=id)
    opp.drop_table(ExampleTable)
