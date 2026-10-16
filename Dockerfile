# Remote MCP server (claude.ai custom connector) — see mcp_server.py and MCP_SETUP.md.
# Package list lives here, not in a requirements file: the local document-security tool encrypts *.txt in this folder.
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONIOENCODING=utf-8
WORKDIR /app
RUN pip install --no-cache-dir \
    "fastmcp==4.1.0" "py-key-value-aio[firestore]==0.4.6" \
    "streamlit>=1.56,<1.60" "pandas>=2.2,<3.0" openpyxl \
    google-api-python-client google-auth
COPY app.py bp_ask.py mcp_server.py ./
COPY tests/smoke_test.py tests/regression_live.py tests/
CMD ["python", "mcp_server.py"]
