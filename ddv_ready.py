# ddv_ready.py  — Louvre DDV 快速掃描（週一/三/五/日 + 自動重試）
import asyncio, random
from datetime import datetime
import httpx, pandas as pd, streamlit as st

API_ENDPOINT = "https://www.ticketlouvre.fr/louvre/api/RemotingService.cfc?method=doJson"

MAX_CONCURRENCY = 10
RETRY_UNTIL_SEC = 120
TARGET_WEEKDAYS = {0, 2, 4, 6}  # 週一=0, 週三=2, 週五=4, 週日=6
AUTO_REFRESH_SEC = 0

DDV_CONFIG = {
    "eventCode": "GA",
    "performanceId": "720553",
    "performanceAk": "LVR.EVN21.PRF116669",
    "priceTableId": "1",
}

st.set_page_config(page_title="Louvre DDV Tickets", layout="wide")
st.title("🎟️ Louvre – Droit de visite (DDV)（週一/三/五/日）")

ak = DDV_CONFIG.get("performanceAk", "")
ak_mask = ak[:6] + "..." + ak[-4:] if len(ak) > 10 else ak
st.caption(
    f"eventCode={DDV_CONFIG['eventCode']} • performanceId={DDV_CONFIG['performanceId']} "
    f"• priceTableId={DDV_CONFIG['priceTableId']} • performanceAk={ak_mask}"
)

now = datetime.now()
m_list = [now.month, now.month + 1, now.month + 2, now.month + 3]
if now.day >= 15:
    m_list.insert(0, now.month + 4)
months = sorted({(m - 1) % 12 + 1 for m in m_list})

c1, c2, c3 = st.columns(3)
with c1:
    month = st.selectbox("選擇月份 / Month", months, index=0)
with c2:
    concurrency = st.slider("並行數 / Concurrency", 5, 40, MAX_CONCURRENCY, 1)
with c3:
    retry_window = st.selectbox("重試時間（秒）", [60, 120, 180, 300], index=[60,120,180,300].index(RETRY_UNTIL_SEC))

def make_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=API_ENDPOINT,
        http2=True,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json, text/plain, */*",
           
