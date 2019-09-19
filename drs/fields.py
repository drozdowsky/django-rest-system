import copy
import re

REGEX_TYPE = type(re.compile(''))


class SkipField(Exception):
    pass


class empty:
    """represents no data"""
    pass


class Field(object):
    _creation_counter = 0

    def __init__(self, source=None, default=empty):
        self._creation_counter = Field._creation_counter
        Field._creation_counter += 1

        self.source = source
        self.default = default
        # These are set up by `.bind()` when the field is added to a serializer.
        self.field_name = None
        self.parent = None

    def bind(self, field_name, parent):
        """
        Initializes the field name and parent for the field instance.
        Called when a field is added to the parent serializer instance.
        """

        # In order to enforce a consistent style, we error if a redundant
        # 'source' argument has been used. For example:
        # my_field = serializer.CharField(source='my_field')
        assert self.source != field_name, (
            "It is redundant to specify `source='%s'` on field '%s' in "
            "serializer '%s', because it is the same as the field name. "
            "Remove the `source` keyword argument." %
            (field_name, self.__class__.__name__, parent.__class__.__name__)
        )

        self.field_name = field_name
        self.parent = parent

        # self.source should default to being the same as the field name.
        if self.source is None:
            self.source = field_name

        # self.source_attrs is a list of attributes that need to be looked up
        # when serializing the instance, or populating the validated data.
        if self.source == '*':
            self.source_attrs = []
        else:
            self.source_attrs = self.source.split('.')

    def get_value(self, dictionary):
        return dictionary.get(self.field_name, empty)

    def get_attribute(self, instance):
        return get_attribute(instance, self.source_attrs)

    def get_default(self):
        if self.default is empty or getattr(self.root, 'partial', False):
            # No default, or this is a partial update.
            raise SkipField()
        if callable(self.default):
            if hasattr(self.default, 'set_context'):
                self.default.set_context(self)
            return self.default()
        return self.default

    def validate_empty_values(self, data):
        if data is empty:
            if getattr(self.root, 'partial', False):
                raise SkipField()
            return (True, self.get_default())

        if data is None:
            return (True, None)

        return (False, data)

    def to_internal_value(self, data):
        raise NotImplementedError(
            '{cls}.to_internal_value() must be implemented.'.format(
                cls=self.__class__.__name__
            )
        )

    def to_representation(self, value):
        raise NotImplementedError(
            '{cls}.to_representation() must be implemented for field '
            '{field_name}. If you do not need to support write operations '
            'you probably want to subclass `ReadOnlyField` instead.'.format(
                cls=self.__class__.__name__,
                field_name=self.field_name,
            )
        )

    @property
    def root(self):
        """
        Returns the top-level serializer for this field.
        """
        root = self
        while root.parent is not None:
            root = root.parent
        return root

    @property
    def context(self):
        """
        Returns the context as passed to the root serializer on initialization.
        """
        return getattr(self.root, '_context', {})

    def __new__(cls, *args, **kwargs):
        """
        When a field is instantiated, we store the arguments that were used,
        so that we can present a helpful representation of the object.
        """
        instance = super().__new__(cls)
        instance._args = args
        instance._kwargs = kwargs
        return instance

    def __deepcopy__(self, memo):
        """
        When cloning fields we instantiate using the arguments it was
        originally created with, rather than copying the complete state.
        """
        # Treat regexes and validators as immutable.
        # See https://github.com/encode/django-rest-framework/issues/1954
        # and https://github.com/encode/django-rest-framework/pull/4489
        args = [
            copy.deepcopy(item) if not isinstance(item, REGEX_TYPE) else item
            for item in self._args
        ]
        kwargs = {
            key: (copy.deepcopy(value, memo) if (key not in ('validators', 'regex')) else value)
            for key, value in self._kwargs.items()
        }
        return self.__class__(*args, **kwargs)

    def __repr__(self):
        return representation.field_repr(self)
