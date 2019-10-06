## Abstract

Add mypy (and other type checker) support for Django.


## Specification

Currently, there are two ways to accomplish that:
1. Provide type annotations right in the Django codebase.

Pros:
* much more accurate types
* easier to keep them in sync with the code changes
* additional value for typechecking of the codebase itself

Cons:
* clutter of the codebase

Django is very dynamic, so some functions have a lot of different signatures, which could not be expressed in the codebase and require `@overload` clauses
https://www.python.org/dev/peps/pep-0484/#function-method-overloading

An example would be a `Field` - it should behave different whether it's invoked on model class, or model instance. Class returns `Field` object itself, and instance resolve field into an underlying python object
```python
# _ST - set type
# _GT - get type
# self: _T -> _T allows mypy to extract type of `self` and return it

class Field(Generic[_ST, _GT])
    @overload
    def __get__(self: _T, instance: None, owner) -> _T: ...
    # Model instance access
    @overload
    def __get__(self, instance: Model, owner) -> _GT: ...
    # non-Model instances
    @overload
    def __get__(self: _T, instance, owner) -> _T: ...
```

2. Store type stubs separately.
https://www.python.org/dev/peps/pep-0484/#stub-files

    Pros:
    * non-invasive change, could be stored / installed as a separate package

    Cons:
    * Out-of-sync with Django itself

    * Hard to test. Mypy (as of now) can't use stub definitions to typecheck codebase itself. There are some solutions to this problem, like
    https://github.com/ambv/retype
    https://github.com/google/pytype/tree/master/pytype/tools/merge_pyi

        but I've miserably failed in making them work for django-stubs and Django, there's a lot of things to consider. There's also a possibility of writing our own solution, shouldn't be too hard.

        django-stubs uses Django test suite to test stubs right now.


## How django-stubs currently implemented

`django-stubs` uses a mix of static analysis provided by mypy, and runtime type inference from Django own introspection facilities.
 For example, newly introduced typechecking of `QuerySet.filter` uses Django _meta API to extract possible lookups for every field, to resolve kwargs like `name__iexact`.


## Current issues and limitations of django-stubs

1. Generic parameters of `QuerySet`.

    For example, we have a model
    ```python
    class User:
        name = models.CharField()
    ```

    1. A simple `QuerySet` which is a result of `User.objects.filter()` returns `QuerySet[User]`.

    2. When we add `values_list('name')` method to the picture, we need to remember (and encode in the generic params) both the fact that it's a `QuerySet` of the `User` model, and that the return item will be a tuple object of `name`.
    So, it becomes `QuerySet[User, Tuple[str]]`.

    3. To implement `.annotate(upper=Upper('name'))` we need to remember all the fields that created from `annotate`, so it becomes
    `QuerySet[User, Tuple[str], TypedDict('upper': str)]`

2. Manager inheritance.

    ```python
    class BaseUser(models.Model):
        class Meta:
            abstract = True

        objects = BaseUserManager()

    class User(BaseUser):
        objects = UserManager()
    ```
    Mypy will flag those `objects` managers as incompatible as they violate Liskov Substitution principle.

3. Generic parameters for `Field`

    ```python
    class User:
        name = models.CharField()
        surname = models.CharField(null=True)
    ```

    `name` and `surname` props are recognized by mypy as generic descriptors. Here's the stub for the `Field`

    ```python
    class Field(Generic[_ST, _GT]):
        def __set__(self, instance, value: _ST) -> None: ...
        # class access
        @overload
        def __get__(self: _T, instance: None, owner) -> _T: ...
        # Model instance access
        @overload
        def __get__(self, instance: Model, owner) -> _GT: ...
        # non-Model instances
        @overload
        def __get__(self: _T, instance, owner) -> _T: ...

    class CharField(Field[_ST, _GT]):
        _pyi_private_set_type: Union[str, int, Combinable]
        _pyi_private_get_type: str
    ```

    In the plugin `django-stubs` dynamically marks `name` and `surname` as `CharField[Optional[Union[str, int, Combinable]], Optional[str]]`. We cannot use (as far as I know),

    ```python
    class CharField(Field[Union[str, int, Combinable], str]):
        pass
    ```
    because then we won't be able to change generic params for `CharField` dynamically.

    And it also creates a UX issue, as `Field` has two generic params which makes zero sense semantically.

4. `BaseManager.from_queryset()`, `QuerySet.as_manager()`

    Not implementable as of now, see
    https://github.com/python/mypy/issues/2813
    https://github.com/python/mypy/issues/7266



