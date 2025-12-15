import traceback
from typing import Iterable, List, Optional
import streamlit as st


class UserFacingError(Exception):
    """Lỗi dùng để hiển thị thông điệp thân thiện cho người dùng cuối."""


def render_error(message: str, exc: Optional[Exception] = None) -> None:
    """Hiển thị lỗi thân thiện và (tuỳ chọn) chi tiết kỹ thuật trong expander."""
    st.error(message)
    if exc is not None:
        with st.expander("Chi tiết kỹ thuật (dành cho đội phát triển)"):
            st.code("".join(traceback.format_exception(exc)), language="text")


def require_columns(df, required: Iterable[str]) -> List[str]:
    """Trả về danh sách cột còn thiếu (nếu có)."""
    required_set = {col.strip().upper() for col in required}
    existing = set(df.columns.str.strip().str.upper())
    return sorted(required_set - existing)


def ensure_required_columns(df, required: Iterable[str]) -> None:
    """Raise UserFacingError nếu thiếu cột bắt buộc."""
    missing = require_columns(df, required)
    if missing:
        raise UserFacingError(
            "Tệp Excel thiếu các cột bắt buộc: " + ", ".join(missing)
        )
