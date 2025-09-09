## Image Lineage

Cartography builds container image lineage by extracting layer information from registries and identifying parent-child relationships based on shared layers.

### How It Works

1. **Layer Extraction**: Uses `docker buildx imagetools inspect` to get layer diff IDs directly from registries (no image download required)

2. **Layer Graph**: Creates a linked list of `ImageLayer` nodes for each image:
   ```
   ECRImage --HEAD--> Layer1 --NEXT--> Layer2 --NEXT--> ... --NEXT--> LayerN <--TAIL-- ECRImage
   ```

3. **Lineage Detection**: Image B is a parent of Image A if B's layers are a prefix of A's layers
   ```
   Parent: [Layer1, Layer2, Layer3]
   Child:  [Layer1, Layer2, Layer3, Layer4, Layer5]
   Result: Child --BUILT_FROM--> Parent
   ```

### Data Sources

**From Registry (via docker buildx):**
- Layer diff IDs (uncompressed sha256 hashes)
- Image digest
- Platform information

**From Trivy (if available):**
- Additional metadata
- Package-to-layer attribution (when provided)

### Graph Model

**Nodes:**
- `ImageLayer`: Individual container layer
  - `id`: Layer diff ID (sha256)
  - `diff_id`: Same as id

**Relationships:**
- `(ImageLayer)-[:NEXT]->(ImageLayer)`: Layer ordering
- `(ECRImage)-[:HEAD]->(ImageLayer)`: First layer
- `(ECRImage)-[:TAIL]->(ImageLayer)`: Last layer
- `(ECRImage)-[:BUILT_FROM]->(ECRImage)`: Parent-child lineage

**Image Properties:**
- `length`: Number of layers
- `platforms`: Supported architectures

### Requirements

- Docker with buildx support (included in Docker Desktop 18.09+)
- Registry credentials (handled automatically for ECR via AWS CLI)

### Configuration

```bash
# Enable lineage (default: true)
cartography --selected-modules trivy --trivy-build-lineage true

# Specify platform for multi-arch images
cartography --selected-modules trivy --trivy-platform linux/amd64
```

### Cleanup

Layers are shared across images and cleaned up intelligently:
- Stale relationships are removed
- Orphaned layers (not referenced by any image) are deleted
- Shared layers are preserved
