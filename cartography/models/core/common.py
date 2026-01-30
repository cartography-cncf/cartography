class PropertyRef:
    """
    Represents properties on cartography nodes and relationships.

    PropertyRefs allow dynamically generated Neo4j ingestion queries to set values for node or
    relationship properties from either:

    A) A field on the dict being processed (``set_in_kwargs=False``; default)
    B) A single variable provided by a keyword argument (``set_in_kwargs=True``)

    Cartography takes lists of Python dicts and loads them to Neo4j using these property references
    to map data appropriately.

    Examples:
        >>> # Basic property reference from data dict
        >>> prop_ref = PropertyRef('name')
        >>> str(prop_ref)  # Returns: 'item.name'

        >>> # Property reference from kwargs
        >>> prop_ref = PropertyRef('lastupdated', set_in_kwargs=True)
        >>> str(prop_ref)  # Returns: '$lastupdated'

        >>> # Property with extra index for frequent queries
        >>> prop_ref = PropertyRef('arn', extra_index=True)

        >>> # Case-insensitive matching
        >>> prop_ref = PropertyRef('username', ignore_case=True)

        >>> # One-to-many relationship
        >>> prop_ref = PropertyRef('role_arns', one_to_many=True)

    Note:
        PropertyRef instances are typically used within CartographyNodeSchema and
        CartographyRelSchema definitions to specify how data should be mapped
        from source dictionaries to Neo4j graph properties.
    """

    def __init__(
        self,
        name: str,
        set_in_kwargs=False,
        extra_index=False,
        ignore_case=False,
        fuzzy_and_ignore_case=False,
        one_to_many=False,
    ):
        """
        Initialize a PropertyRef instance.

        Args:
            name (str): The name of the property.
            set_in_kwargs (bool, optional): If True, the property is not defined on the data dict,
                and we expect to find the property in the kwargs. If False, looks for the property
                in the data dict. Defaults to False.
            extra_index (bool, optional): If True, creates an index for this property name.
                Available for properties that are queried frequently. Defaults to False.
            ignore_case (bool, optional): If True, performs a case-insensitive match when comparing
                the value of this property during relationship creation. Only has effect as part of
                a TargetNodeMatcher, and is not supported for sub resource relationships.
                Defaults to False.
            fuzzy_and_ignore_case (bool, optional): If True, performs a fuzzy + case-insensitive
                match when comparing the value of this property using the ``CONTAINS`` operator.
                Only has effect as part of a TargetNodeMatcher and is not supported for sub
                resource relationships. Defaults to False.
            one_to_many (bool, optional): Indicates that this property creates one-to-many
                associations. If True, this property ref points to a list stored on the data dict
                where each item is an ID. Only has effect as part of a TargetNodeMatcher and is
                not supported for sub resource relationships. Defaults to False.

        Examples:
            Case-insensitive matching for GitHub usernames:
                GitHub usernames can have both uppercase and lowercase characters, but GitHub
                treats usernames as case-insensitive. If your company's internal personnel
                database stores GitHub usernames all as lowercase, you would need to perform
                a case-insensitive match between your company's record and your cartography
                catalog of GitHubUser nodes::

                    PropertyRef('username', ignore_case=True)

            One-to-many associations for AWS IAM instance profiles:
                AWS IAM instance profiles can be associated with one or more roles. When calling
                describe-iam-instance-profiles, the ``Roles`` field contains a list of all roles
                that the profile is associated with::

                    class InstanceProfileSchema(Schema):
                        target_node_label: str = 'AWSRole'
                        target_node_matcher: TargetNodeMatcher = make_target_node_matcher({
                            'arn': PropertyRef('Roles', one_to_many=True),
                        })

                This searches for AWSRoles to attach by checking if each role's ``arn`` field
                is in the ``Roles`` list of the data dict.

        Note:
            - ``one_to_many`` has no effect on matchlinks.
            - ``extra_index`` is available for properties that will be queried frequently.
            - The ``id`` and ``lastupdated`` properties automatically have indexes created by
              ``ensure_indexes()``.
            - All properties included in target node matchers automatically have indexes created.

        Raises:
            ValueError: If ``ignore_case`` is used together with ``fuzzy_and_ignore_case``.
            ValueError: If ``one_to_many`` is used together with ``ignore_case`` or
                ``fuzzy_and_ignore_case``.
        """
        self.name = name
        self.set_in_kwargs = set_in_kwargs
        self.extra_index = extra_index
        self.ignore_case = ignore_case
        self.fuzzy_and_ignore_case = fuzzy_and_ignore_case
        self.one_to_many = one_to_many

        if self.fuzzy_and_ignore_case and self.ignore_case:
            raise ValueError(
                f'Error setting PropertyRef "{self.name}": ignore_case cannot be used together with'
                "fuzzy_and_ignore_case. Pick one or the other.",
            )

        if self.one_to_many and (self.ignore_case or self.fuzzy_and_ignore_case):
            raise ValueError(
                f'Error setting PropertyRef "{self.name}": one_to_many cannot be used together with '
                "`ignore_case` or `fuzzy_and_ignore_case`.",
            )

    def _parameterize_name(self) -> str:
        """
        Prefix the property name with a '$' for keyword arguments.

        This method creates a parameterized version of the property name that can be
        used in Neo4j queries when the property value comes from keyword arguments
        rather than the data dictionary.

        Returns:
            str: The property name prefixed with '$'.

        See Also:
            :meth:`__repr__`: For details on how this is used in query building.
        """
        return f"${self.name}"

    def __repr__(self) -> str:
        """
        Return the string representation used in Neo4j query building.

        The ``querybuilder.build_ingestion_query()`` generates a Neo4j batched ingestion query
        of the form ``UNWIND $DictList AS item [...]``. This method provides the appropriate
        property reference format based on whether the property value comes from the data
        dictionary or from keyword arguments.

        Returns:
            str: Either ``item.<property_name>`` if ``set_in_kwargs`` is False, or
                ``$<property_name>`` if ``set_in_kwargs`` is True.

        Examples:
            >>> # Property from data dictionary
            >>> prop_ref = PropertyRef('name')
            >>> str(prop_ref)
            'item.name'

            >>> # Property from keyword arguments
            >>> prop_ref = PropertyRef('lastupdated', set_in_kwargs=True)
            >>> str(prop_ref)
            '$lastupdated'
        """
        return (
            f"item.{self.name}" if not self.set_in_kwargs else self._parameterize_name()
        )
