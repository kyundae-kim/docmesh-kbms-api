### Environment
- `uv` is already installed and available in the execution environment.  
- Prefer `uv` for all Python package and dependency operations.

### Dev Docker compose
- .devcontainer/docker-compose.minio.yml

### What to avoid
- lazy import.
- optional dependency.
- sqlalchemy core style.
- access uv.lock.
- kwargs override.
- regression testing for document.
- build python package.
