"""
Context management for synchronization jobs.

This module provides context objects with well-documented fields that can be passed
between different parts of the sync job and used to get parameters for job queries.
The context system allows for clean parameter passing and enables module-specific
context extensions through subclassing.

The general workflow is:
1. Create a base Context with common parameters (like update_tag)
2. Pass it to sync modules that need access to these parameters
3. Optionally extend it with module-specific context using subclassing

Note:
    The context pattern promotes clean separation of concerns by allowing each
    module to access only the parameters it needs while maintaining a consistent
    interface for parameter passing throughout the sync pipeline.
"""


class Context:
    """
    Base context class for synchronization job parameters.

    This class provides a standardized way to pass parameters between different
    parts of the sync job. It can be subclassed to create module-specific contexts
    that extend the base functionality with additional fields.

    Attributes:
        update_tag: A timestamp or identifier used to track when data was last updated.
            This is typically used in Neo4j queries to identify and clean up stale data.

    Examples:
        Basic usage:

        >>> ctx = Context(update_tag=1642784400)
        >>> print(ctx.update_tag)
        1642784400

        Creating a module-specific context:

        >>> class DatabaseContext(Context):
        ...     def __init__(self, update_tag, db_host, db_port):
        ...         super().__init__(update_tag)
        ...         self.db_host = db_host
        ...         self.db_port = db_port
        ...
        ...     @classmethod
        ...     def from_context(cls, context, db_host, db_port):
        ...         return cls(context.update_tag, db_host, db_port)

        >>> base_ctx = Context(update_tag=1642784400)
        >>> db_ctx = DatabaseContext.from_context(base_ctx, "localhost", 5432)
        >>> print(db_ctx.update_tag, db_ctx.db_host, db_ctx.db_port)
        1642784400 localhost 5432

    Note:
        Subclasses should implement a ``from_context`` class method to enable easy
        conversion from a base context to the specialized context. This pattern
        maintains consistency across different context types.
    """

    def __init__(self, update_tag):
        """
        Initialize a new Context instance.

        Args:
            update_tag: A timestamp or identifier used to track data freshness.
                This is typically used in cleanup queries to identify stale data.
        """
        self.update_tag = update_tag

    def _to_dict(self):
        """
        Convert the context to a dictionary with uppercase keys.

        Returns:
            dict: A dictionary with uppercase keys and the context's attribute values.
        """
        return {k.upper(): v for k, v in self.__dict__.items()}
