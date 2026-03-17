"""create_agent_locations_table

Revision ID: f5g6h7i8j9k0
Revises: e4f5g6h7i8j9
Create Date: 2026-03-17 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from geoalchemy2 import Geography

# revision identifiers, used by Alembic.
revision: str = 'f5g6h7i8j9k0'
down_revision: Union[str, Sequence[str], None] = 'e4f5g6h7i8j9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. 启用PostGIS扩展
    op.execute('CREATE EXTENSION IF NOT EXISTS postgis')

    # 2. 创建agent_locations表
    op.create_table(
        'agent_locations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('latitude', sa.Numeric(precision=10, scale=8), nullable=False),
        sa.Column('longitude', sa.Numeric(precision=11, scale=8), nullable=False),
        sa.Column('address', sa.String(length=500), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('latitude >= -90 AND latitude <= 90', name='chk_latitude'),
        sa.CheckConstraint('longitude >= -180 AND longitude <= 180', name='chk_longitude')
    )

    # 3. 创建普通索引
    op.create_index('idx_agent_locations_agent_id', 'agent_locations', ['agent_id'])
    op.create_index('idx_agent_locations_is_active', 'agent_locations', ['is_active'])
    op.create_index('idx_agent_locations_display_order', 'agent_locations', ['display_order'])

    # 4. 添加地理位置列（PostGIS GEOGRAPHY类型）
    op.execute("""
        ALTER TABLE agent_locations
        ADD COLUMN location GEOGRAPHY(POINT, 4326)
    """)

    # 5. 更新location列（从latitude和longitude生成）
    op.execute("""
        UPDATE agent_locations
        SET location = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
    """)

    # 6. 创建空间索引
    op.execute("""
        CREATE INDEX idx_agent_locations_location_gist
        ON agent_locations USING GIST (location)
    """)

    # 7. 创建触发器：自动更新location列和updated_at字段
    op.execute("""
        CREATE OR REPLACE FUNCTION update_agent_location_geography()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.location = ST_SetSRID(ST_MakePoint(NEW.longitude, NEW.latitude), 4326);
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER trigger_update_agent_location_geography
        BEFORE INSERT OR UPDATE OF latitude, longitude ON agent_locations
        FOR EACH ROW
        EXECUTE FUNCTION update_agent_location_geography();
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # 1. 删除触发器和函数
    op.execute('DROP TRIGGER IF EXISTS trigger_update_agent_location_geography ON agent_locations')
    op.execute('DROP FUNCTION IF EXISTS update_agent_location_geography()')

    # 2. 删除表（会自动删除索引）
    op.drop_table('agent_locations')

    # 注意：不删除PostGIS扩展，因为可能有其他表在使用
