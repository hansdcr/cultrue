#!/usr/bin/env python3
"""
生成迭代6 Agent管理的数据库表关系图
使用matplotlib绘制ER图
"""
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path
import platform

# 配置中文字体
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'PingFang SC', 'Heiti SC', 'STHeiti', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题


def draw_table(ax, x, y, width, height, title, fields, color):
    """绘制一个表格"""
    # 绘制表格边框
    rect = patches.Rectangle((x, y), width, height, linewidth=2,
                             edgecolor='black', facecolor='white')
    ax.add_patch(rect)

    # 绘制标题背景
    title_height = 0.8
    title_rect = patches.Rectangle((x, y + height - title_height), width, title_height,
                                   linewidth=0, facecolor=color, alpha=0.7)
    ax.add_patch(title_rect)

    # 绘制标题文字
    ax.text(x + width/2, y + height - title_height/2, title,
           ha='center', va='center', fontsize=12, fontweight='bold')

    # 绘制字段
    field_height = (height - title_height) / len(fields)
    for i, field in enumerate(fields):
        field_y = y + height - title_height - (i + 1) * field_height
        # 绘制分隔线
        if i > 0:
            ax.plot([x, x + width], [field_y + field_height, field_y + field_height],
                   'k-', linewidth=0.5, alpha=0.3)
        # 绘制字段文字
        ax.text(x + 0.2, field_y + field_height/2, field,
               ha='left', va='center', fontsize=9, family='monospace')


def draw_arrow(ax, x1, y1, x2, y2, label, color='black', style='solid'):
    """绘制箭头表示关系"""
    arrow_props = dict(
        arrowstyle='->',
        color=color,
        lw=2,
        linestyle=style,
        connectionstyle='arc3,rad=0.3'
    )
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
               arrowprops=arrow_props)

    # 添加标签
    mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
    ax.text(mid_x, mid_y, label, fontsize=8,
           bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8),
           ha='center', va='center')


def create_iteration6_diagram():
    """创建迭代6的ER图"""
    # 创建画布
    fig, ax = plt.subplots(figsize=(16, 12))
    ax.set_xlim(0, 20)
    ax.set_ylim(0, 15)
    ax.axis('off')

    # 添加标题
    ax.text(10, 14.5, '迭代6: Agent管理 - 数据库表关系图',
           ha='center', va='center', fontsize=16, fontweight='bold')

    # 定义表格位置和内容
    # users表（左上）
    users_fields = [
        '🔑 id: UUID',
        'username: VARCHAR',
        'email: VARCHAR',
        'password_hash: VARCHAR',
        'created_at: TIMESTAMP'
    ]
    draw_table(ax, 1, 9, 4, 4, 'users', users_fields, 'lightblue')

    # agents表（右上）
    agents_fields = [
        '🔑 id: UUID',
        '🔒 agent_id: VARCHAR (UNIQUE)',
        'name: VARCHAR',
        'avatar: VARCHAR',
        'description: TEXT',
        'system_prompt: TEXT',
        'model_config: JSONB',
        '⚡ api_key_prefix: VARCHAR(16)',
        'api_key_hash: VARCHAR',
        'is_active: BOOLEAN',
        '🔗 created_by: UUID',
        'created_at: TIMESTAMP',
        'updated_at: TIMESTAMP'
    ]
    draw_table(ax, 15, 7, 4.5, 6, 'agents', agents_fields, 'lightgreen')

    # participants表（中间）
    participants_fields = [
        '🔑 id: UUID',
        'participant_type: VARCHAR(20)',
        '🔗 user_id: UUID (NULLABLE)',
        '🔗 agent_id: UUID (NULLABLE)',
        'created_at: TIMESTAMP',
        '---',
        'CHECK: type匹配ID',
        'UNIQUE: user_id, agent_id'
    ]
    draw_table(ax, 7.5, 6, 5, 5, 'participants\n(中间表)', participants_fields, 'lightyellow')

    # contacts表（下方）
    contacts_fields = [
        '🔑 id: UUID',
        '🔗 owner_id: UUID',
        '🔗 target_id: UUID',
        'contact_type: VARCHAR(20)',
        'alias: VARCHAR',
        'is_favorite: BOOLEAN',
        'last_interaction_at: TIMESTAMP',
        'created_at: TIMESTAMP',
        '---',
        'UNIQUE: (owner_id, target_id)'
    ]
    draw_table(ax, 7, 1, 6, 4.5, 'contacts', contacts_fields, 'lightcoral')

    # 绘制关系箭头
    # agents.created_by -> users.id
    draw_arrow(ax, 15, 10, 5, 11, 'created_by\n(FK)', 'blue', 'dashed')

    # participants.user_id -> users.id
    draw_arrow(ax, 7.5, 9, 5, 10, 'user_id\n(FK, CASCADE)', 'red', 'solid')

    # participants.agent_id -> agents.id
    draw_arrow(ax, 12.5, 9, 15, 10, 'agent_id\n(FK, CASCADE)', 'red', 'solid')

    # contacts.owner_id -> participants.id
    draw_arrow(ax, 9, 5.5, 9.5, 6, 'owner_id\n(FK, CASCADE)', 'darkgreen', 'solid')

    # contacts.target_id -> participants.id
    draw_arrow(ax, 11, 5.5, 10.5, 6, 'target_id\n(FK, CASCADE)', 'darkgreen', 'dashed')

    # 添加图例
    legend_x, legend_y = 0.5, 0.5
    ax.text(legend_x, legend_y + 2.5, '图例说明:', fontsize=10, fontweight='bold')
    ax.text(legend_x, legend_y + 2, '🔑 主键', fontsize=9)
    ax.text(legend_x, legend_y + 1.5, '🔗 外键', fontsize=9)
    ax.text(legend_x, legend_y + 1, '🔒 唯一约束', fontsize=9)
    ax.text(legend_x, legend_y + 0.5, '⚡ 索引字段', fontsize=9)

    # 添加关系说明
    ax.plot([legend_x, legend_x + 1], [legend_y - 0.5, legend_y - 0.5], 'r-', linewidth=2)
    ax.text(legend_x + 1.2, legend_y - 0.5, 'CASCADE删除', fontsize=9, va='center')

    ax.plot([legend_x, legend_x + 1], [legend_y - 1, legend_y - 1], 'b--', linewidth=2)
    ax.text(legend_x + 1.2, legend_y - 1, '可选关系', fontsize=9, va='center')

    plt.tight_layout()
    return fig


def main():
    """主函数"""
    # 创建图表
    fig = create_iteration6_diagram()

    # 确保docs目录存在
    docs_dir = Path(__file__).parent.parent / 'docs'
    docs_dir.mkdir(exist_ok=True)

    # 保存为PNG
    output_path = docs_dir / 'iteration6_tables_relationship.png'
    fig.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close(fig)

    print(f"✅ 图表已生成: {output_path}")
    print("\n📊 表关系说明:")
    print("  - users表: 用户表（已存在）")
    print("  - agents表: Agent表，包含API Key认证信息")
    print("  - participants表: 中间表，统一表示User和Agent")
    print("  - contacts表: 联系人关系表，支持User-User、User-Agent、Agent-Agent关系")
    print("\n🔗 关键关系:")
    print("  1. agents.created_by -> users.id (Agent的创建者)")
    print("  2. participants.user_id -> users.id (CASCADE)")
    print("  3. participants.agent_id -> agents.id (CASCADE)")
    print("  4. contacts.owner_id -> participants.id (CASCADE)")
    print("  5. contacts.target_id -> participants.id (CASCADE)")
    print("\n⚡ 关键字段:")
    print("  - agents.api_key_prefix: API Key前缀，用于快速索引查找")
    print("  - agents.api_key_hash: API Key的bcrypt哈希值")
    print("  - participants.participant_type: 'user' 或 'agent'")
    print("  - contacts.contact_type: 'friend', 'favorite', 'colleague', 'blocked'")
    print("\n💡 双层抽象架构:")
    print("  - 领域层: 使用Actor值对象统一表示User和Agent")
    print("  - 数据库层: 使用Participant中间表保证数据完整性")
    print("  - 仓储层: 自动管理Actor ↔ Participant转换")


if __name__ == '__main__':
    main()
