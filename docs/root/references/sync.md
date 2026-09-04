# Sync

## CLI

```{eval-rst}
.. automodule:: cartography.cli
    :synopsis:
    :members:
    :special-members: __init__
    :undoc-members:
    :show-inheritance:
    :member-order: groupwise
```

## Sync API

```{eval-rst}
.. automodule:: cartography.sync
    :synopsis:
    :members:
    :special-members: __init__
    :undoc-members:
    :show-inheritance:
    :member-order: groupwise
```

## Utils

```{eval-rst}
.. automodule:: cartography.util
    :synopsis:
    :members:
    :special-members: __init__
    :undoc-members:
    :show-inheritance:
    :member-order: groupwise
```

### AWS utils

AWS-specific helpers live outside `cartography.util` so that importing the core package
does not pull `boto3` and `botocore` into every cartography process.

```{eval-rst}
.. automodule:: cartography.util.aws
    :synopsis:
    :members:
    :special-members: __init__
    :undoc-members:
    :show-inheritance:
    :member-order: groupwise
```

### Lazy imports

An intel module's config gate has to run before its provider SDK loads, otherwise a sync
with no credentials for that provider still pays for the import. These helpers let an
entry point keep its imports at the top of the file while deferring the actual import to
the moment the module does work.

```{eval-rst}
.. automodule:: cartography.util.lazy
    :synopsis:
    :members:
    :special-members: __init__
    :undoc-members:
    :show-inheritance:
    :member-order: groupwise
```

## Stats
```{eval-rst}
.. automodule:: cartography.stats
    :synopsis:
    :members:
    :special-members: __init__
    :undoc-members:
    :show-inheritance:
    :member-order: groupwise
```
