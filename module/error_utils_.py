import traceback
from typing import Callable, Iterable, List, Optional

import streamlit as st


class UserFacingError(Exception):
    """Lỗi dùng để hiển thị thông điệp thân thiện cho người dùng cuối."""

def render_error(message: str, exc: Optional[Exception] = None) -> None:
    """Hiển thị lỗi thân thiện và (tuỳ chọn) chi tiết kỹ thuật trong expander."""
    st.error(message)
    if exc is not None:
        with st.expander("Chi tiết kỹ thuật (dành cho đội phát triển)"):
            st.code("".join(traceback.format_exception(exc)), language="text")

def _should_reraise(exc: Exception) -> bool:
    """Trả về True nếu đó là exception đặc biệt của Streamlit cần propagate."""

    try:
        from streamlit.runtime.scriptrunner import RerunException, StopException

        return isinstance(exc, (RerunException, StopException))
    except Exception:
        return False


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


def normalize_columns(df):
    """Chuẩn hoá tên cột: bỏ khoảng trắng, viết hoa để giảm xung đột khi nhập file."""

    df.columns = df.columns.str.strip().str.upper()
    return df


def run_with_user_error(fn: Callable[[], None], context: str) -> None:
    """Wrapper để hiển thị thông báo lỗi thân thiện cho toàn bộ UI chính.

    Parameters
    ----------
    fn: Callable
        Hàm thực thi (không đối số) cần bọc lỗi.
    context: str
        Mô tả ngắn gọn cho hành động, dùng trong thông báo lỗi chung.
    """

    try:
        fn()
    except UserFacingError as exc:
        render_error(str(exc))
    except Exception as exc:
        if _should_reraise(exc):
            raise

        render_error(
            f"Đã xảy ra lỗi khi {context}. Vui lòng kiểm tra dữ liệu đầu vào và thử lại.",
            exc,
        )
