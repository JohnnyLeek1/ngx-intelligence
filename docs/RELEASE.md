# Release Process

This document describes how to create releases for ngx-intelligence.

## Overview

The project uses GitHub Actions to automatically build and publish Docker images for every commit to `main` and for all tagged releases. Images are published to GitHub Container Registry (ghcr.io).

## Creating a Release

### 1. Prepare the Release

Before creating a release, ensure:

- [ ] All tests pass locally
- [ ] Documentation is up to date
- [ ] CHANGELOG is updated (if you maintain one)
- [ ] Version numbers are updated where applicable

### 2. Create and Push a Tag

Use semantic versioning (e.g., v1.2.3):

```bash
# Create a new tag
git tag -a v1.0.0 -m "Release v1.0.0"

# Push the tag to GitHub
git push origin v1.0.0
```

### 3. Automated Workflows

Once the tag is pushed, GitHub Actions will automatically:

1. **Build Docker Images** (`.github/workflows/docker-build.yml`)
   - Builds backend and frontend images
   - Supports multi-platform builds (amd64, arm64)
   - Tags images with:
     - `v1.0.0` (exact version)
     - `v1.0` (major.minor)
     - `v1` (major)
     - `latest` (for main branch tags)

2. **Create GitHub Release** (`.github/workflows/release.yml`)
   - Generates release notes with changelog
   - Links to Docker images
   - Provides quick start instructions

### 4. Verify the Release

After the workflows complete:

1. Check the [Actions tab](https://github.com/JohnnyLeek1/ngx-intelligence/actions) for successful builds
2. Verify the [Releases page](https://github.com/JohnnyLeek1/ngx-intelligence/releases) has the new release
3. Check that Docker images are available:
   ```bash
   docker pull ghcr.io/johnnyleek1/ngx-intelligence-backend:v1.0.0
   docker pull ghcr.io/johnnyleek1/ngx-intelligence-frontend:v1.0.0
   ```

## Version Tagging Strategy

### Semantic Versioning

We follow [Semantic Versioning](https://semver.org/) (MAJOR.MINOR.PATCH):

- **MAJOR** (v1.0.0 → v2.0.0): Breaking changes, incompatible API changes
- **MINOR** (v1.0.0 → v1.1.0): New features, backwards-compatible
- **PATCH** (v1.0.0 → v1.0.1): Bug fixes, backwards-compatible

### Pre-release Versions

For pre-release versions, use suffixes:

```bash
# Alpha release
git tag -a v1.0.0-alpha.1 -m "Release v1.0.0-alpha.1"

# Beta release
git tag -a v1.0.0-beta.1 -m "Release v1.0.0-beta.1"

# Release candidate
git tag -a v1.0.0-rc.1 -m "Release v1.0.0-rc.1"
```

Pre-release tags will be marked as "pre-release" in GitHub Releases.

## Docker Image Tags

For each release, the following Docker tags are created:

### Version Tag (e.g., v1.2.3)

```bash
ghcr.io/johnnyleek1/ngx-intelligence-backend:v1.2.3
ghcr.io/johnnyleek1/ngx-intelligence-frontend:v1.2.3
```

### Major.Minor Tag (e.g., v1.2)

```bash
ghcr.io/johnnyleek1/ngx-intelligence-backend:v1.2
ghcr.io/johnnyleek1/ngx-intelligence-frontend:v1.2
```

This tag is updated with each patch release.

### Major Tag (e.g., v1)

```bash
ghcr.io/johnnyleek1/ngx-intelligence-backend:v1
ghcr.io/johnnyleek1/ngx-intelligence-frontend:v1
```

This tag is updated with each minor and patch release.

### Latest Tag

```bash
ghcr.io/johnnyleek1/ngx-intelligence-backend:latest
ghcr.io/johnnyleek1/ngx-intelligence-frontend:latest
```

Points to the latest stable release from the main branch.

### Branch Tags

```bash
ghcr.io/johnnyleek1/ngx-intelligence-backend:main
ghcr.io/johnnyleek1/ngx-intelligence-frontend:develop
```

Updated with each commit to the respective branch.

## Hotfix Releases

For critical bug fixes that need to be released quickly:

```bash
# Create a hotfix branch from the tag
git checkout -b hotfix/v1.0.1 v1.0.0

# Make your fixes
git add .
git commit -m "Fix critical bug"

# Tag the hotfix
git tag -a v1.0.1 -m "Hotfix v1.0.1: Fix critical bug"

# Push the tag
git push origin v1.0.1

# Merge back to main
git checkout main
git merge hotfix/v1.0.1
git push origin main
```

## Rolling Back a Release

If a release has critical issues:

1. **Delete the tag locally and remotely:**
   ```bash
   git tag -d v1.0.0
   git push origin :refs/tags/v1.0.0
   ```

2. **Delete the GitHub Release:**
   - Go to [Releases](https://github.com/JohnnyLeek1/ngx-intelligence/releases)
   - Find the release and click "Delete"

3. **Note:** Docker images cannot be deleted from ghcr.io, but they will no longer be referenced. Users can pin to a specific working version.

## Testing Releases Locally

Before creating a public release, test the release process:

```bash
# Create a test tag
git tag -a v0.0.0-test -m "Test release"

# Push to trigger workflows
git push origin v0.0.0-test

# Verify the images work
docker pull ghcr.io/johnnyleek1/ngx-intelligence-backend:v0.0.0-test
docker pull ghcr.io/johnnyleek1/ngx-intelligence-frontend:v0.0.0-test

# Clean up test tag
git tag -d v0.0.0-test
git push origin :refs/tags/v0.0.0-test
```

## Troubleshooting

### Build Fails

1. Check the [Actions tab](https://github.com/JohnnyLeek1/ngx-intelligence/actions) for error logs
2. Common issues:
   - Dependency installation failures
   - Test failures
   - Docker build errors
   - Platform-specific build issues

### Images Not Available

1. Verify GitHub Actions completed successfully
2. Check package permissions in GitHub settings
3. Ensure you're logged in to ghcr.io:
   ```bash
   echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
   ```

### Release Notes Not Generated

1. Check that the release workflow completed
2. Verify the tag format matches `v*.*.*`
3. Ensure the repository has write permissions for the GitHub token

## GitHub Actions Configuration

### Required Secrets

The workflows use built-in GitHub secrets:

- `GITHUB_TOKEN`: Automatically provided by GitHub Actions
  - Used for pushing to ghcr.io
  - Used for creating releases

No additional secrets need to be configured.

### Workflow Files

- `.github/workflows/docker-build.yml`: Builds and pushes Docker images
- `.github/workflows/release.yml`: Creates GitHub releases with notes

## Best Practices

1. **Always test locally** before creating a release tag
2. **Use semantic versioning** consistently
3. **Write clear commit messages** - they become part of release notes
4. **Update documentation** before releases
5. **Test pre-built images** before announcing a release
6. **Communicate breaking changes** clearly in release notes

## Release Checklist

- [ ] All tests pass (`pytest`, `npm test`)
- [ ] Build works locally (`docker-compose build`)
- [ ] Documentation updated
- [ ] Version bumped (if maintaining version files)
- [ ] Tag created with proper format (`v*.*.*`)
- [ ] Tag pushed to GitHub
- [ ] GitHub Actions workflows completed successfully
- [ ] Docker images available on ghcr.io
- [ ] GitHub Release created
- [ ] Release notes reviewed
- [ ] Announced to users (if applicable)