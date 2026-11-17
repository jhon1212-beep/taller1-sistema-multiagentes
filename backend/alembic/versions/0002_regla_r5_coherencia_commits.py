"""R5: admite la regla de coherencia entre commit y código en alerta.regla.

Revision ID: 0002
Revises: 0001
"""
from typing import Sequence, Union

from alembic import op

revision: str = '0002'
down_revision: Union[str, Sequence[str], None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NOMBRE = 'ck_alerta_regla_valida'


def upgrade() -> None:
    op.drop_constraint(op.f(NOMBRE), 'alerta', type_='check')
    op.create_check_constraint(op.f(NOMBRE), 'alerta', "regla IN ('R1', 'R2', 'R3', 'R4', 'R5')")


def downgrade() -> None:
    # Las alertas R5 no caben en la restricción anterior: se borran antes de volver.
    op.execute("DELETE FROM alerta WHERE regla = 'R5'")
    op.drop_constraint(op.f(NOMBRE), 'alerta', type_='check')
    op.create_check_constraint(op.f(NOMBRE), 'alerta', "regla IN ('R1', 'R2', 'R3', 'R4')")
