"""initial schema (8 tables per spec §19)

Revision ID: 0001
Revises:
Create Date: 2026-05-09

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "etf_list",
        sa.Column("etf_id", sa.String(10), primary_key=True),
        sa.Column("etf_name", sa.String(100), nullable=False),
        sa.Column("issuer", sa.String(100), nullable=False),
        sa.Column("disclosure_url", sa.Text, nullable=False),
        sa.Column("aum_url", sa.Text),
        sa.Column("aum_source", sa.String(10), nullable=False, server_default="inline"),
        sa.Column("crawler_mode", sa.String(20), nullable=False, server_default="light"),
        sa.Column("fallback_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("added_date", sa.Date, nullable=False, server_default=sa.func.current_date()),
        sa.Column("last_success_date", sa.Date),
        sa.Column("last_known_aum", sa.BigInteger),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "holding_records",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("etf_id", sa.String(10), sa.ForeignKey("etf_list.etf_id"), nullable=False),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("stock_id", sa.String(10), nullable=False),
        sa.Column("shares_held", sa.BigInteger, nullable=False),
        sa.Column("weight_pct", sa.Numeric(6, 4)),
        sa.Column("aum", sa.BigInteger),
        sa.Column("aum_source", sa.String(20)),
        sa.Column("is_new_position", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("data_status", sa.String(20), nullable=False, server_default="normal"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("etf_id", "date", "stock_id"),
    )
    op.create_index("idx_holding_date", "holding_records", ["date"])
    op.create_index("idx_holding_stock_date", "holding_records", ["stock_id", "date"])
    op.create_index("idx_holding_etf_date", "holding_records", ["etf_id", "date"])

    op.create_table(
        "consensus_scores",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("stock_id", sa.String(10), nullable=False),
        sa.Column("stock_name", sa.String(100)),
        sa.Column("breadth_score", sa.Numeric(5, 4)),
        sa.Column("depth_score", sa.Numeric(5, 4)),
        sa.Column("accumulate_etf_count", sa.Integer),
        sa.Column("total_amount", sa.BigInteger),
        sa.Column("consecutive_days", sa.Integer),
        sa.Column("signal_tag", sa.String(20)),
        sa.Column("reduction_breadth", sa.Numeric(5, 4)),
        sa.Column("reduction_etf_count", sa.Integer),
        sa.Column("reduction_consec", sa.Integer),
        sa.Column("risk_tag", sa.String(20)),
        sa.Column("param_breadth_thr", sa.Numeric(5, 4)),
        sa.Column("param_depth_thr", sa.Numeric(5, 4)),
        sa.Column("param_consec_days", sa.Integer),
        sa.Column("param_red_breadth", sa.Numeric(5, 4)),
        sa.Column("param_red_consec", sa.Integer),
        sa.Column("n_etfs", sa.Integer),
        sa.Column("data_status", sa.String(20), nullable=False, server_default="normal"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("date", "stock_id"),
    )
    op.create_index("idx_consensus_date", "consensus_scores", ["date"])
    op.create_index(
        "idx_consensus_signal",
        "consensus_scores",
        ["date", "signal_tag"],
        postgresql_where=sa.text("signal_tag IS NOT NULL"),
    )

    op.create_table(
        "signal_records",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("stock_id", sa.String(10), nullable=False),
        sa.Column("stock_name", sa.String(100)),
        sa.Column("signal_type", sa.String(20), nullable=False),
        sa.Column("signal_tag", sa.String(20), nullable=False),
        sa.Column("breadth_score", sa.Numeric(5, 4)),
        sa.Column("depth_score", sa.Numeric(5, 4)),
        sa.Column("consecutive_days", sa.Integer),
        sa.Column("notified_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("date", "stock_id", "signal_type"),
    )

    op.create_table(
        "backtest_runs",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("start_date", sa.Date, nullable=False),
        sa.Column("end_date", sa.Date, nullable=False),
        sa.Column("holding_days", sa.Integer, nullable=False),
        sa.Column("breadth_threshold", sa.Numeric(5, 4), nullable=False),
        sa.Column("depth_threshold", sa.Numeric(5, 4), nullable=False),
        sa.Column("consecutive_days", sa.Integer, nullable=False),
        sa.Column("target_stocks", postgresql.ARRAY(sa.String)),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "backtest_results",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("run_id", sa.BigInteger, sa.ForeignKey("backtest_runs.id"), nullable=False),
        sa.Column("stock_id", sa.String(10), nullable=False),
        sa.Column("stock_name", sa.String(100)),
        sa.Column("trigger_date", sa.Date, nullable=False),
        sa.Column("buy_date", sa.Date, nullable=False),
        sa.Column("buy_price", sa.Numeric(12, 2)),
        sa.Column("sell_date", sa.Date, nullable=False),
        sa.Column("sell_price", sa.Numeric(12, 2)),
        sa.Column("return_rate", sa.Numeric(8, 4)),
        sa.Column("is_valid", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("invalid_reason", sa.String(100)),
        sa.Column("breadth_score", sa.Numeric(5, 4)),
        sa.Column("depth_score", sa.Numeric(5, 4)),
        sa.Column("price_series", postgresql.JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "system_config",
        sa.Column("key", sa.String(100), primary_key=True),
        sa.Column("value", sa.Text, nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "crawl_logs",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("etf_id", sa.String(10), sa.ForeignKey("etf_list.etf_id"), nullable=False),
        sa.Column("crawl_date", sa.Date, nullable=False),
        sa.Column("crawler_used", sa.String(20)),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("records_count", sa.Integer),
        sa.Column("duration_ms", sa.Integer),
        sa.Column("error_message", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # 預設門檻參數
    op.execute(
        """
        INSERT INTO system_config (key, value, description) VALUES
            ('breadth_threshold',           '0.6', '加碼廣度門檻'),
            ('depth_threshold',             '0.6', '加碼深度門檻'),
            ('consecutive_days',            '3',   '加碼連續天數門檻'),
            ('sliding_window',              '5',   '滑動窗口天數'),
            ('reduction_breadth_threshold', '0.6', '減碼廣度門檻'),
            ('reduction_consecutive_days',  '3',   '減碼連續天數門檻');
        """
    )


def downgrade() -> None:
    op.drop_table("crawl_logs")
    op.drop_table("system_config")
    op.drop_table("backtest_results")
    op.drop_table("backtest_runs")
    op.drop_table("signal_records")
    op.drop_index("idx_consensus_signal", table_name="consensus_scores")
    op.drop_index("idx_consensus_date", table_name="consensus_scores")
    op.drop_table("consensus_scores")
    op.drop_index("idx_holding_etf_date", table_name="holding_records")
    op.drop_index("idx_holding_stock_date", table_name="holding_records")
    op.drop_index("idx_holding_date", table_name="holding_records")
    op.drop_table("holding_records")
    op.drop_table("etf_list")
