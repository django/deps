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

Add mypy (and other type checkers) support for Django. 

## Motivation

### Internal use

1. Inline documentation
    * Lower barrier to entry.
    * Easier to think about what's going on and edgecases

2. Catching hard-to-find bugs
    * not all codebase is covered with tests, so `None` related functionality is never tested, because nobody actually thought about it being used that way. 

3. Another testsuite to prevent regressions
    * accidental changes break other parts of the codebase
    * easier review, easier to understand what contributor meant to do 

### External use

1. Typechecking of user codebases. 

    * mypy is increasingly popular in proprietary projects.

        * shorten time for new developer to get up to speed with the codebase. 
        * prevent bugs / regressions, basically another test suite. 

        * add scalability to the codebase

    * third-party apps that use / modify Django internal tools would benefit from typechecking

### IDE support

* go to definition, find usages, refactorings.

Example: 

```python
class User(models.Model):
    name = models.CharField()

# other file
def get_username(user):
    return user.name
```

Rename `name` -> `username`. Any IDE will have a hard time understanding that `user` param is a `User` instance. Trivial with type annotation. 

```python
def get_username(user: User):
    return user.name  # will be renamed into user.username
```
    
* interactive typechecking of passed params and return values

* support in vscode/emacs/vim (microsoft's python-language-server), PyCharm (internal implementation of the typechecker), pyre, mypy

* inline annotations -> IDE is always up to date with code changes (no `typeshed` syncing)

## Implementation

### Migration path

1. Add `py.typed` file inside the Django top-level module, to mark that it has inline annotations. 
See https://www.python.org/dev/peps/pep-0561/#packaging-type-information

2. Add `__class_getitem__` implementation to classes which need to support generic parameters. For example, for `QuerySet` class (`QuerySet[MyModel]` annotation)
https://docs.python.org/3/reference/datamodel.html#emulating-generic-types

    It's just

    ```python
    def __class_getitem__(cls, *args, **kwargs):
        return cls
    ```
    
    (some additional parameters checking could be added later)

3. Add `mypy` to CI, like it's done in this PR for DRF
https://github.com/encode/django-rest-framework/pull/6988 

    Make it pass. It would require some type annotations around the codebase, some cases should be silenced via `# type: ignore`
    https://mypy.readthedocs.io/en/latest/common_issues.html#spurious-errors-and-locally-silencing-the-checker

4. Merge `django-stubs` annotations into the codebase. This one could be done incrementally, on file-per-file basis. 

5. For complex cases use `.pyi` counterpart (described below). To be able to remain in sync with the codebase, `merge-pyi` tool invocation must be added to the CI.
https://github.com/google/pytype/tree/master/pytype/tools/merge_pyi


### Complementing with `.pyi` stub files for complex cases

There are some cases, for which stores type information inline creates more problems than benefits. 

Django is very dynamic, some functions have more than on relationship between argument types and return value type. For those cases, there's an `@overload` clause available
https://www.python.org/dev/peps/pep-0484/#function-method-overloading

For these cases, type information should be stored in the separate stub file. 
https://www.python.org/dev/peps/pep-0484/#stub-files

Examples: 

* `@overload` clauses

    Django is very dynamic, some functions have more than one relationship between argument types and return value type. For those cases, there's an `@overload` clause available
    https://www.python.org/dev/peps/pep-0484/#function-method-overloading

    Example is `__get__` method of the `Field`. 
    1. Returns underlying python type when called on instance. 
    2. Returns `Field` instance when called on class. 

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

* `**kwargs` for `Field` classes

    Mypy (and other typecheckers) doesn't understand `**kwargs`. There are ways to make it work via `TypedDict` and type aliases, but it's hard to read. 

    ```python
    class CharField(Field):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.validators.append(validators.MaxLengthValidator(self.max_length))
    ```

    How it would look like, if it would be inline: 

    ```python
    class CharField(Field):
        def __init__(
            self,
            verbose_name: Optional[Union[str, bytes]] = ...,
            name: Optional[str] = ...,
            primary_key: bool = ...,
            max_length: Optional[int] = ...,
            unique: bool = ...,
            blank: bool = ...,
            null: bool = ...,
            db_index: bool = ...,
            default: Any = ...,
            editable: bool = ...,
            auto_created: bool = ...,
            serialize: bool = ...,
            unique_for_date: Optional[str] = ...,
            unique_for_month: Optional[str] = ...,
            unique_for_year: Optional[str] = ...,
            choices: Optional[_FieldChoices] = ...,
            help_text: str = ...,
            db_column: Optional[str] = ...,
            db_tablespace: Optional[str] = ...,
            validators: Iterable[_ValidatorCallable] = ...,
            error_messages: Optional[_ErrorMessagesToOverride] = ...,
        ): 
            super().__init__(*args, **kwargs)
            self.validators.append(validators.MaxLengthValidator(self.max_length))
    ```

### Mypy plugin support

Not all Django behavious expressable via type system - Django will have to provide those features via mypy plugin. Most of those are implemented in `django-stubs`, inside `mypy_django_plugin` sub-package. 

Those are features implemented so far in the `mypy_django_plugin`:

1. Fields and managers inference.

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

3. RelatedField's support, support for different apps in the RelatedField's `to=` argument

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
    CustomProfile().user  # will be correctly inferred as 'some_custom_app.models.User'
    ```

4. Support for unannotated third-party base models, 
    ```python
    class User(ThirdPartyModel):
        pass
    ```
    will be recognized as correct model. 

6. settings support
    ```python
    from django.conf import settings
    settings.ALLOWED_HOSTS  # inferred as Sequence[str]
    ```

7. `get_user_model()` correctly infers current user model class.


### Limitations of the plugin

0. `mypy_django_plugin` uses a mix of static and dynamic analysis to support Django features. It basically does `django.setup()` inside to gain access to all the _meta API and `Apps` information. 

    * users needs to be aware of that, and work on preventing side-effects of `django.setup()`, if there's any

    * typechecking of Django app with invalid syntax or semantics will crash the plugin

    Possible solution: reimplement all Django logic of traversing models in apps for the plugin. 

1. Manager inheritance. 

    ```python
    class BaseUser(models.Model):
        class Meta:
            abstract = True

        objects = BaseUserManager()

    class User(BaseUser):
        objects = UserManager()
    ```
    Mypy will flag those `objects` managers as incompatible as they violate Liskov Substitution principle. 

    Possible solution: https://github.com/python/mypy/issues/7468

2. Generic parameters for `Field`

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

    Possible solution: whole bunch of `@overload` statements over `__new__` method. 

3. `BaseManager.from_queryset()`, `QuerySet.as_manager()`

    Not implementable as of now, see 
    https://github.com/python/mypy/issues/2813
    https://github.com/python/mypy/issues/7266

