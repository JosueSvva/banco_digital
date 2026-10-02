"""adiciona protecao ao cpf

Revision ID: 362037263da3
Revises: 836f9b4d2c4f
Create Date: 2026-10-02 17:47:43.151586

"""

from typing import Sequence, Union
from pathlib import Path
import os

from alembic import op
import sqlalchemy as sa
from dotenv import load_dotenv


revision: str = '362037263da3'
down_revision: Union[str, Sequence[str], None] = '836f9b4d2c4f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    caminho_projeto = Path(__file__).resolve().parents[2]
    caminho_env = caminho_projeto / ".env"

    load_dotenv(caminho_env)


    chave = os.getenv("CPF_ENCRYPTION_KEY")

    if not chave:
        raise RuntimeError("CPF_ENCRYPTION_KEY nao configurada.")

    op.add_column(
        'usuario',
        sa.Column('cpf_criptografado', sa.LargeBinary(), nullable=True)
    )

    op.add_column(
        'usuario',
        sa.Column('cpf_hash', sa.String(), nullable=True)
    )

    # Criptografa os CPFs existentes e cria o hash para consultas.
    op.execute(
         sa.text("""
        UPDATE usuario
        SET
            cpf_criptografado = pgp_sym_encrypt(
                cpf,
                :chave
            ),
            cpf_hash = encode(
                digest(cpf, 'sha256'),
                'hex'
            )
        WHERE cpf IS NOT NULL;
    """).bindparams(chave=chave)
)

    op.create_unique_constraint(
        'usuario_cpf_hash_key',
        'usuario',
        ['cpf_hash']
    )

    op.drop_column('usuario', 'cpf')


def downgrade() -> None:

    op.add_column(
        'usuario',
        sa.Column('cpf', sa.String(), nullable=True)
    )

    # O CPF original não pode ser recuperado automaticamente
    # porque a migration de downgrade não deve guardar a chave.
    op.drop_column('usuario', 'cpf_hash')
    op.drop_column('usuario', 'cpf_criptografado')

    op.alter_column(
        'usuario',
        'cpf',
        nullable=False
    )

    op.create_unique_constraint(
        'usuario_cpf_key',
        'usuario',
        ['cpf']
    )