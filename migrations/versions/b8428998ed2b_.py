"""empty message

Revision ID: b8428998ed2b
Revises: 2d3d374c25c8
Create Date: 2021-04-19 00:08:22.650430

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b8428998ed2b'
down_revision = '2d3d374c25c8'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('File',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=1000), nullable=True),
    sa.Column('fileType', sa.String(length=100), nullable=True),
    sa.Column('data', sa.LargeBinary(), nullable=True),
    sa.Column('assignmentId', sa.Integer(), nullable=False),
    sa.Column('moduleId', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['assignmentId'], ['Assignment.id'], ),
    sa.ForeignKeyConstraint(['moduleId'], ['Module.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('File')
    # ### end Alembic commands ###
