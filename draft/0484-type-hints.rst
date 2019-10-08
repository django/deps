# DEP 0484: Static type checking for Django

|  |  |
| --- | --- |
| **DEP:** | 0484 |
| **Author:** | Maksim Kurnikov |
| **Implementation team:** | Maksim Kurnikov |
| **Shepherd:** | Carlton Gibson |
| **Type:** | Feature |
| **Status:** | Draft |
| **Created:** | 2019-10-08 |
| **Last modified:** | 2019-10-08 |

## Abstract

Add mypy (and other type checker) support for Django.


## Specification

I propose to add type hinting support for Django via mypy and PEP484. All at once it's too big of a change, so I want to propose an incremental migration, using both stub files and inline type annotations.

https://www.python.org/dev/peps/pep-0484/#stub-files

Back in a day, there was some friction about gradually improving the type checking coverage of different parts of Python ecosystem. So PEP561 was accepted based on the discussion.

It defines how PEP484-based typecheckers would look for a type annotations information across the different places.

https://www.python.org/dev/peps/pep-0561

Specifically, it defines a "Type Checker Method Resolution Order"
https://www.python.org/dev/peps/pep-0561/#type-checker-module-resolution-order

> 1. Stubs or Python source manually put in the beginning of the path. Type checkers SHOULD provide this to allow the user complete control of which stubs to use, and to patch broken stubs/inline types from packages. In mypy the $MYPYPATH environment variable can be used for this.
> 2. User code - the files the type checker is running on.
> 3. Stub packages - these packages SHOULD supersede any installed inline package. They can be found at foopkg-stubs for package foopkg.
> 4. Inline packages - if there is nothing overriding the installed package, and it opts into type checking, inline types SHOULD be used.
> 5. Typeshed (if used) - Provides the stdlib types and several third party libraries.

What is means for Django, it that we can split type annotations into stub files, and inline annotations. Where there will be a corresponding `.pyi` file, mypy would use that, otherwise fallback to inline type annotations.

There's an existing `django-stubs` package where most of the Django codebase files have a `.pyi` counterpart with type annotations.

https://github.com/typeddjango/django-stubs

It also has some plugin code, which takes care of the dynamic nature of Django models.

It's desirable that this package would be usable alongside the Django type annotations migration.


### Incremental migration path:
1. Add `py.typed` file inside the Django top-level module, to mark that it has inline annotations.
See https://www.python.org/dev/peps/pep-0561/#packaging-type-information

2. Add `__class_getitem__` implementation for the `QuerySet` class to support generic instantiation.

3. Decide on file-by-file based, whether it's appropriate to have inline type annotation, or have it separate for the sake of readability. For those files, merge annotations from `django-stubs`, removing those files in the library.

4. Adopt `django-stubs` as an official Django library to catch more bugs, push users a bit more towards type annotations and prepare them for a change.

5. Do some work on a `merge-pyi` side to make it complete enough for `django-stubs` and Django. For that, we can react out for mypy folks and work with them.

6. Add stubs checking CI step:
    1. Use `merge-pyi` to merge `django-stubs` into the Django codebase.
    2. Run `mypy` and report errors.

    This would allow us to keep `django-stubs` in sync with Django codebase, and prevent false-positives to happen.

7. Based on gained experience, merge more stubs into the codebase.


## Notes

### Overload clutter

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


### How django-stubs currently implemented

`django-stubs` uses a mix of static analysis provided by mypy, and runtime type inference from Django own introspection facilities.
 For example, newly introduced typechecking of `QuerySet.filter` uses Django _meta API to extract possible lookups for every field, to resolve kwargs like `name__iexact`.

 ### What is currently implemented (and therefore possible)

1. Fields inference.

    ```python
    class User(models.Model):
        name = models.CharField()
        surname = models.CharField(null=True)

    user = User()
    user.name  # inferred type: str
    user.surname  # inferred type: Optional[str]

    # objects is added to every model
    User.objects.get()  # inferred type: User
    User.objects.filter(unknown=True)  # will fail with "no such field"
    User.objects.filter(name=True)  # will fail with "incompatible types 'bool' and 'str'"
    User.objects.filter(name__iexact=True)  # will fail with "incompatible types 'bool' and 'str'"
    User.objects.filter(name='hello')  # passes
    User.objects.filter(name__iexact='hello')  # passes
    ```

2. Typechecking for `__init__` and `create()`
    ```python
    class User(models.Model):
        name = models.CharField()
    User(name=1)  # fail
    User(unknown=1)  # fail
    User(name='hello')  # pass
    ```
    same for `create()` with different `Optional`ity conditions.


3. RelatedField's support, support for different apps in the RelatedField's to= argument

    ```python
    class User:
        pass
    class Profile:
        user = models.OneToOneField(to=User, related_name='profile')

    Profile().user  # inferred type 'User'
    User().profile  # inferred type 'Profile'
    ```

    ```python
    class CustomProfile:
        user = models.ForeignKey(to='some_custom_app.User')
    CustomProfile().user  # will be correctly inferred as 'some_custom_app.User'
    ```

4. Support for unannotated third-party base models,
    ```python
    class User(ThirdPartyModel):
        pass
    ```
    will be recognized as correct model.

5. `values`, `values_list` support

    ```python
    class User:
        name = models.CharField()
        surname = models.CharField()
    User.objects.values_list('name', 'surname')[0]  # will return Tuple[str, str]
    ```

6. settings support
    ```python
    from django.conf import settings
    settings.INSTALLED_APPS  # will be inferred as Sequence[str]
    ```

7. `get_user_model()` infers current model class


### Current issues and limitations of django-stubs

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

