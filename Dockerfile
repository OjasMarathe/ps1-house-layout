# House-Design Pipeline — serving image (PS1 exterior + PS2 interior, Z3-verified)
FROM python:3.11-slim

WORKDIR /app

# 1) Dependencies (cached layer — only re-runs if requirements change)
COPY requirements-serve.txt .
RUN pip install --no-cache-dir -r requirements-serve.txt

# 2) Application code — only the modules the serving pipeline actually needs
#    (LLM agents / Streamlit UI are intentionally left out of the serving image)
COPY serve_app.py artifacts.py verifier_tool.py verifier_z3.py optimizer_z3.py \
     interior_verifier_z3.py codeloader.py plot.py constraints.py rooms.py \
     templates.py interior_fill.py \
     roof_tool.py roof_agent.py roof_vents.py roof_elevations.py \
     roof_verifier_z3.py roof_dxf.py roof_render.py pipeline_io.py ./
COPY citycodes/ ./citycodes/

EXPOSE 8000

# Container-level health check (Kubernetes also probes /health independently)
HEALTHCHECK --interval=15s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health').status==200 else 1)"

# One uvicorn worker per container; scale by running MORE pods, not more workers
CMD ["uvicorn", "serve_app:app", "--host", "0.0.0.0", "--port", "8000"]
