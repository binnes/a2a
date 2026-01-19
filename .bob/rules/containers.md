# Container Rules

## Container Tooling

**CRITICAL RULE**: Always use Podman for container operations. Never reference Docker.

### Requirements

1. **Podman Only**: All container operations must use Podman
   - Use `podman` command instead of `docker`
   - Use `podman-compose` instead of `docker-compose`
   - Reference Podman in documentation and scripts

2. **Containerfile Naming**: Container specifications must be named `Containerfile`, not `Dockerfile`
   - Use `Containerfile` as the default name
   - Never use `Dockerfile` in new code
   - When refactoring, rename `Dockerfile` to `Containerfile`

3. **Compose Files**: Use standard compose format but reference Podman
   - File can be named `podman-compose.yml` or `compose.yml`
   - Include comments indicating Podman usage
   - Ensure compatibility with podman-compose

### Examples

Good:
```bash
# Build container
podman build -f Containerfile -t myapp:latest .

# Run with compose
podman-compose up -d

# Push to registry
podman push myapp:latest
```

Bad:
```bash
# Don't use docker
docker build -f Dockerfile -t myapp:latest .
docker-compose up -d
```

### Documentation

- Always mention Podman in setup instructions
- Provide Podman installation links
- Explain Podman advantages when relevant
- Never suggest Docker as an alternative

### Enforcement

- Review all scripts for docker references
- Check all container specifications are named Containerfile
- Ensure documentation uses Podman terminology
- Update existing code during refactoring