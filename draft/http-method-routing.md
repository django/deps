---
DEP: HTTP Method Routing
Author: Joshua Massover
Implementation Team: 
Shepherd: 
Status: Draft
Type: Feature
Created: 2025-11-23
Last-Modified: 2025-11-23
---
# DEP XXXX: HTTP Method Routing

Table of Contents
- [Abstract](#abstract)
- [Specification](#specification)
- [Motivation](#motivation)
- [Rationale](#rationale)
- [Backwards Compatibility](#backwards-compatibility)
- [Reference Implementation](#reference-implementation)
- [Copyright](#copyright)

## Abstract

This doesn't work right now because the first url pattern will always resolve.

```python
urlpatterns = [
    path('pet', views.pet_list_view),
    path('pet', views.pet_create_view),
]
```

This can be solved by routing on class methods right now:

```python
urlpatterns = [
    path('pet', views.PetView.as_view())
]
```

Also, it can be solved functionally by making our own "routing" view:

```python
urlpatterns = [
    path('pet', list_router(get=views.pet_list_view, post=views.pet_create_view),
]
```

It also seems like it would be nice if this "just worked" (or some other chosen syntax):

```python
urlpatterns = [
    path('pet', views.pet_list_view, methods=['GET'],),
    path('pet', views.pet_create_view, methods=['POST']),
]
```

## Specification

### URL Definition

Http method routing can be defined two ways:

```python
urlpatterns = [
    path.get('pet', views.pet_list_view),
    # or
    path('pet', views.pet_list_view, methods=['GET']),
]
```

The list of `methods` supported are: get, post, put, patch, delete, head and options

### 405 Handling

If a path fails to resolve due to just the method, the resolver will raise a 
`Resolver405({"path": path, "method": method})`. There is 405 response handling in places where django already 
had 404 response handling. The `response_for_exception` for exception function supports the new `Http405` exception,
including support for a `handler405` error view or `405.html` template.

## Motivation

Http method routing extends the existing urlpatterns to route by method. It provides a simple way to organize view
callbacks by both path and method. This pattern has proved successful in many other python frameworks. 
This is DEP brings the same pattern to Django.

## Rationale

Method routing is an extension of the existing url routing handled at the url module. With the introduction of http 
method routing, the difference between decorator routing and url module is cosmetic. It's not worth introducing a 
new pattern for view registration in django; consistency is more important.

The `path.method` syntax was chosen to mirror the popular `app.method` syntax but for django url patterns. Since 
`path.method` is restricted to 1 method per callback, the path callable also takes a `methods` argument to support 
multiple methods to the same callback.

## Backwards Compatibility

### No changes to existing urls without methods

All existing paths without http method routing should continue to work. There is no
plan to make methods a requirement for path definitions. There are existing functional ways to 
limit the methods accessible by a view (`require_http_methods`, `require_GET`, `require_POST`, `require_safe`).

```python
@require_GET
def pet_create_view(request):
    ...
```

Using http method routing and decorator methods could lead to unwanted behavior but there is no plan to warn or raise.

```python
path('pet', views.pet_create_view, methods=['POST']),
```

### Path callable compatibility

For compatibility with the existing `path` callable and to enable the new `path.method` syntax, a `_Path` callable is 
used. The `_Path` callable defines a method for each http method (eg. `_Path.get`, `_Path.post`), and two callable objects
are instantiated in the global namespace for `re_path` and `path`. The path callables now accept a new optional 
`methods` argument which defaults to `None`.

### resolve compatibility

Django provides a few public resolving functions that need to maintain existing behavior. 

[resolve](https://docs.djangoproject.com/en/5.2/ref/urlresolvers/#resolve)


```python
urlpatterns = [
    path("no-methods", view.no_methods_view),
    path.get("pet", view.pet_list),
    path.post("pet", view.pet_create),
]
```

```
# if a path with no methods is resolved without a method, it must resolve.
resolve("/no-methods") -> ✅

# if a path with no methods is resolved with any method, it must resolve because it's up to the view to handle it
resolve("/no-methods", method="get") -> ✅

# if a path is defined with methods and resolved with no method, it must not resolve.
resolve("/pet") -> ❌

# if a path is defined with methods and the resolving method matches, it must resolve
resolve("/pet", method="get") -> ✅
resolve("/pet", method="post") -> ✅

# if a path is defined with methods and the resolving method does not match, it must not resolve
resolve("/pet", method="put") -> ❌
```

## Reference Implementation

https://github.com/massover/django/pull/1

## Copyright

This document has been placed in the public domain per the Creative
Commons CC0 1.0 Universal license
(<http://creativecommons.org/publicdomain/zero/1.0/deed>).

(All DEPs must include this exact copyright statement.)
