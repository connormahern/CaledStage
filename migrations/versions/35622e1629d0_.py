"""empty message

Revision ID: 35622e1629d0
Revises: 51fcd0b4886c
Create Date: 2021-04-21 22:20:32.579008

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '35622e1629d0'
down_revision = '51fcd0b4886c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('File', sa.Column('assignmentId', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('File', 'assignmentId')
    # ### end Alembic commands ###