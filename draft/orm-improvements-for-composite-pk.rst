=========================================================
DEP : ORM Fields and related improvement for composite PK
=========================================================

:DEP: 0201
:Author: Asif Saif Uddin
:Implementation Team: Asif Saif Uddin, django core team
:Shepherd: Django Core Team
:Status: Draft
:Type: Feature
:Created: 2017-3-2
:Last-Modified: 2017-00-00

.. contents:: Table of Contents
   :depth: 3
   :local:


Abstract
========
Django's ORM is a powerful tool which suits perfectly most use-cases,
however, there are cases where having exactly one primary key column per
table induces unnecessary redundancy.

One such case is the many-to-many intermediary model. Even though the pair
of ForeignKeys in this model identifies uniquely each relationship, an
additional field is required by the ORM to identify individual rows. While
this isn't a real problem when the underlying database schema is created
by Django, it becomes an obstacle as soon as one tries to develop a Django
application using a legacy database.

Since there is already a lot of code relying on the pk property of model
instances and the ability to use it in QuerySet filters, it is necessary
to implement a mechanism to allow filtering of several actual fields by
specifying a single filter.

The proposed solution is using Virtualfield type, CompositeField. This field
type will enclose several real fields within one single object.


Motivation
==========
This DEP aims to improve different part of django ORM and other associated parts of django to support composite primary key in django. There were several attempt to fix this problem and several ways to implement this. There are two existing dep for solving this problem, but the aim of this dep is to incorporate Michal Petrucha's works  suggestions/discussions from other related tickets and lesson learned from previous works. The main motivation of this Dep's approach is to improve django ORM's Field API
and design everything as much simple and small as possible to be able to implement separately.


Key concerns of New Approach to implement ``CompositeField``
==============================================================
1. Split out Field API to ConcreteField, BaseField etc and change on ORM based on the splitted API.
2. Introduce new standalone well defined ``VirtualField``
3. Incorporate ``VirtualField`` related changes in django
4. Refactor ForeignKey based on ``VirtualField`` and ``ConcreteField`` etc NEW Field API
5. Figure out other cases where true virtual fields are needed.
6. Refactor all RelationFields [OneToOne, ManyToMany...] based on ``VirtualField`` and new Field API based ForeignKey
7. Refactor GenericForeignKey based on ``VirtualField`` based refactored ForeignKey 
8. Change ForeignObjectRel subclasses to real field instances. (For example,
 ForeignKey generates a ManyToOneRel in the related model). The Rel instances are already returned from get_field(), but they aren't yet field subclasses.
9. Allow direct usage of ForeignObjectRel subclasses. In certain cases it can be advantageous to be able to define reverse relations directly. For example, see ​https://github.com/akaariai/django-reverse-unique.
 
10. Make changes to migrations framework to work properly with Reafctored Field
   API.

11. Make sure new class based Index API ise used properly with refactored Field
   API.

12. Consider Database Contraints work of lan-foote and 

13. SubField/AuxilaryField

14. Update in AutoField


Porting previous work on top of master
======================================

The first major task of this project is to take the code written as part
of GSoC 2013 and compare it aganist master to have Idea of valid part. 

The order in which It was implemented few years ago was to implement
``CompositeField`` first and then a refactor of ``ForeignKey`` which
is required to make it support ``CompositeField``. This turned out to be
inefficient with respect to the development process, because some parts of
the refactor broke the introduced ``CompositeField`` functionality,
meaning that it was needed effectively reimplement parts of it again.

Also, some abstractions introduced by the refactor made it possible to
rewrite certain parts in a cleaner way than what was necessary for
``CompositeField`` alone (e.g. database creation or certain features of
``model._meta``).

I am convinced that a better approach would be to Improve Field API and later
imlement VirtualField type to first do the required refactor of ``ForeignKey``
and implement CompositeField as the next step. This will result in a better 
maintainable development branch and a cleaner revision history, making it easier
to review the work before its eventual inclusion into Django.


New split out Field API
=========================
1. BaseField:
-------------
Base structure for all Field types in django ORM wheather it is Concrete
or VirtualField

2. ConcreteField:
-----------------
ConcreteField will have all the common attributes of a Regular concrete field

3. Field:
---------
Presence base Field class with should refactored using BaseField and ConcreteField.
If it is decided to provide the optional virtual type to regular fields then VirtualField's features can also be added to specific fields.

4. VirtualField:
----------------
A true stand alone virtula field will be added to the system to be used to solve some long standing design limitations of django orm. initially RelationFields, GenericRelations etc will be benefitted by using VirtualFields and later CompositeField
or any virtual type field can be benefitted from VirtualField.

5. RelationField:
-----------------


6. CompositeField:
------------------
A composite field can be implemented based on BaseField and VirtualField to solve
the CompositeKey/Multi column PrimaryKey issue.


Introduce standalone ``VirtualField``
=====================================



Changes in ``ForeignKey``
=========================

Currently ``ForeignKey`` is a regular concrete field which manages both
the raw value stored in the database and the higher-level relationship
semantics. Managing the raw value is simple enough for simple
(single-column) targets. However, in the case of a composite target field,
this task becomes more complex. The biggest problem is that many parts of
the ORM work under the assumption that for each database column there is a
model field it can assign the value from the column to. While it might be
possible to lift this restriction, it would be a really complex project by
itself.

On the other hand, there is the abstraction of virtual fields working on
top of other fields which is required for this project anyway. The way
forward would be to use this abstraction for relationship fields.
Currently, ``ForeignKey`` (and by extension ``OneToOneField``) is the only
field whose ``name`` and ``attname`` differ, where ``name`` stores the
value dictated by the semantics of the field and ``attname`` stores the
raw value from the database.

We can use this to our advantage and put an auxiliary field into the
``attname`` of each ``ForeignKey``, which would be of the same database
type as the target field, and turn ``ForeignKey`` into a virtual field on
top of the auxiliary field. This solution has the advantage that it
offloads the need to manage the raw database value off ``ForeignKey`` and
uses a field specifically intended for the task.

In order to keep this backwards compatible and avoid the need to
explicitly create two fields for each ``ForeignKey``, the auxiliary field
needs to be created automatically during the phase where a model class is
created by its metaclass. Initially I implemented this as a method on
``ForeignKey`` which takes the target field and creates its copy, touches
it up and adds it to the model class. However, this requires performing
special tasks with certain types of fields, such as ``AutoField`` which
needs to be turned into an ``IntegerField`` or ``CompositeField`` which
requires copying its enclosed fields as well.

A better approach is to add a method such as ``create_auxiliary_copy`` on
``Field`` which would create all new field instances and add them to the
appropriate model class.

One possible problem with these changes is that they change the contents
of ``_meta.fields`` in each model out there that contains a relationship
field. For example, if a model contains the following fields::

    ['id',
     'name',
     'address',
     'place_ptr',
     'rating',
     'serves_hot_dogs',
     'serves_pizza',
     'chef']

where ``place_ptr`` is a ``OneToOneField`` and ``chef`` is a
``ForeignKey``, after the change it will contain the following list::

    ['id',
     'name',
     'address',
     'place_ptr',
     'place_ptr_id',
     'rating',
     'serves_hot_dogs',
     'serves_pizza',
     'chef',
     'chef_id']

This causes a lot of failures in the Django test suite, because there are
a lot of tests relying on the contents of ``_meta.fields`` or other
related attributes/properties. (Actually, this example is taken from one
of these tests,
``model_inheritance.tests.ModelInheritanceTests.test_multiple_table``.)
Fixing these is fairly simple, all they need is to add the appropriate
``__id`` fields. However, this raises a concern of how ``_meta`` is
regarded. It has always been a private API officially, but everyone uses
it in their projects anyway. I still think the change is worth it, but it
might be a good idea to include a note about the change in the release
notes. 


Changes in ``RelationField``
=============================


Summary of ``CompositeField``
=============================

This section summarizes the basic API as established in the proposal for
GSoC 2011 [1]_.

A ``CompositeField`` requires a list of enclosed regular model fields as
positional arguments, as shown in this example::

    class SomeModel(models.Model):
        first_field = models.IntegerField()
        second_field = models.CharField(max_length=100)
        composite = models.CompositeField(first_field, second_field)

The model class then contains a descriptor for the composite field, which
returns a ``CompositeValue`` which is a customized namedtuple, the
descriptor accepts any iterable of the appropriate length. An example
interactive session::

    >>> instance = new SomeModel(first_field=47, second_field="some string")
    >>> instance.composite
    CompositeObject(first_field=47, second_field='some string')
    >>> instance.composite.first_field
    47
    >>> instance.composite[1]
    'some string'
    >>> instance.composite = (74, "other string")
    >>> instance.first_field, instance.second_field
    (74, 'other string')

``CompositeField`` supports the following standard field options:
``unique``, ``db_index``, ``primary_key``. The first two will simply add a
corresponding tuple to ``model._meta.unique_together`` or
``model._meta.index_together``. Other field options don't make much sense
in the context of composite fields.

Supported ``QuerySet`` filters will be ``exact`` and ``in``. The former
should be clear enough, the latter is elaborated in a separate section.

It will be possible to use a ``CompositeField`` as a target field of
``ForeignKey``, ``OneToOneField`` and ``ManyToManyField``. This is
described in more detail in the following section.



Alternative Approach of compositeFiled
=======================================



``__in`` lookups for ``CompositeField``
=======================================

The existing implementation of ``CompositeField`` handles ``__in`` lookups
in the generic, backend-independent ``WhereNode`` class and uses a
disjunctive normal form expression as in the following example::

    SELECT a, b, c FROM tbl1, tbl2
    WHERE (a = 1 AND b = 2 AND c = 3) OR (a = 4 AND b = 5 AND c = 6);

The problem with this solution is that in cases where the list of values
contains tens or hundreds of tuples, this DNF expression will be extremely
long and the database will have to evaluate it for each and every row,
without a possibility of optimizing the query.

Certain database backends support the following alternative::

    SELECT a, b, c FROM tbl1, tbl2
    WHERE (a, b, c) IN [(1, 2, 3), (4, 5, 6)];

This would probably be the best option, but it can't be used by SQLite,
for instance. This is also the reason why the DNF expression was
implemented in the first place.

In order to support this more natural syntax, the ``DatabaseOperations``
needs to be extended with a method such as ``composite_in_sql``.

However, this leaves the issue of the inefficient DNF unresolved for
backends without support for tuple literals. For such backends, the
following expression is proposed::

    SELECT a, b, c FROM tbl1, tbl2
    WHERE EXISTS (SELECT a1, b1, c1, FROM (SELECT 1 as a, 2 as b, 3 as c
                                           UNION SELECT 4, 5, 6)
                  WHERE a1=1 AND b1=b AND c1=c);

Since both syntaxes are rather generic and at least one of them should fit
any database backend directly, a new flag will be introduced,
``DatabaseFeatures.supports_tuple_literals`` which the default
implementation of ``composite_in_sql`` will consult in order to choose
between the two options.


``contenttypes`` and ``GenericForeignKey``
==========================================


It's fairly easy to represent composite values as strings. Given an
``escape`` function which uniquely escapes commas, something like the
following works quite well::

    ",".join(escape(value) for value in composite_value)

However, in order to support JOINs generated by ``GenericRelation``, we
need to be able to reproduce exactly the same encoding using an SQL
expression which would be used in the JOIN condition.

Luckily, while thus encoded strings need to be possible to decode in
Python (for example, when retrieving the related object using
``GenericForeignKey`` or when the admin decodes the primary key from URL),
this isn't necessary at the database level. Using SQL we only ever need to
perform this in one direction, that is from a tuple of values into a
string.

That means we can use a generalized version of the function
``django.contrib.admin.utils.quote`` which replaces each unsafe
character with its ASCII value in hexadecimal base, preceded by an escape
character. In this case, only two characters are unsafe -- comma (which is
used to separate the values) and an escape character (which I arbitrarily
chose as '~').

To reproduce this encoding, all values need to be cast to strings and then
for each such string two calls to the ``replace`` functions are made::

    replace(replace(CAST (`column` AS text), '~', '~7E'), ',', '~2C')

According to available documentation, all four supported database backends
provide the ``replace`` function. [2]_ [3]_ [4]_ [5]_

Even though the ``replace`` function seems to be available in all major
database servers (even ones not officially supported by Django, including
MSSQL, DB2, Informix and others), this is still probably best left to the
database backend and will be implemented as
``DatabaseOperations.composite_value_to_text_sql``.

One possible pitfall of this implementation might be that it may not work
with any column type that isn't an integer or a text string due to a
simple fact – the string the database would cast it to will probably
differ from the one Python will use. However, I'm not sure there's
anything we can do about this, especially since the string representation
chosen by the database may be specific for each database server. Therefore
I'm inclined to declare ``GenericRelation`` unsupported for models with a
composite primary key containing any special columns. This should be
extremely rare anyway.


Database introspection, ``inspectdb``
=====================================

There are three main goals concerning database introspection in this
project. The first is to ensure the output of ``inspectdb`` remains the
same as it is now for models with simple primary keys and simple foreign
key references, or at least equivalent. While this shouldn't be too
difficult to achieve, it will still be regarded with high importance.

The second goal is to extend ``inspectdb`` to also create a
``CompositeField`` in models where the table contains a composite primary
key. This part shouldn't be too difficult,
``DatabaseIntrospection.get_primary_key_column`` will be renamed to
``get_primary_key`` which will return a tuple of columns and in case the
tuple contains more than one element, an appropriate ``CompositeField``
will be added. This will also require updating
``DatabaseWrapper.check_constraints`` for certain backends since it uses
``get_primary_key_column``.

The third goal is to also make ``inspectdb`` aware of composite foreign
keys. This will need a rewrite of ``get_relations`` which will have to
return a mapping between tuples of columns instead of single columns. It
should also ensure each tuple of columns pointed to by a foreign key gets
a ``CompositeField``. This part will also probably require some changes in
other backend methods as well, especially since each backend has a unique
tangle of introspection methods.

This part requires a tremendous amount of work, because practically every
single change needs to be done four times and needs separate research of
the specific backend in question. Therefore I can't promise to deliver full support
for all features mentioned in this section for all backends. I'd say
backwards compatibility is a requirement, recognition of composite primary
keys is a highly wanted feature that I'll try to implement for as many
backends as possible and recognition of composite foreign keys would be a
nice extra to have for at least one or two backends.

I'll be implementing the features for the individual backends in the
following order: PostgreSQL, MySQL, SQLite and Oracle. I put PostgreSQL
first because, well, this is the backend with the best support in Django
(and also because it is the one where I'd actually use the features I'm
proposing). Oracle comes last because I don't have any way to test it and
I'm afraid I'd be stabbing in the dark anyway. Of the two remaining
backends I put MySQL first for two reasons. First, I don't think people
need to run ``inspectdb`` on SQLite databases too often (if ever). Second,
on MySQL the task seems marginally easier as the database has
introspection features other than just “give me the SQL statement used to
create this table”, whose parsing is most likely going to be a complete
mess.

All in all, extending ``inspectdb`` features is a tedious and difficult
task with shady outcome, which I'm well aware of. Still, I would like to
try to at least implement the easier parts for the most used backends. It
might quite possibly turn out that I won't manage to implement more than
composite primary key detection for PostgreSQL. This is the reason I keep
this as one of the last features I intend to work on, as shown in the
timeline. It isn't a necessity, we can always just add a note to the docs
that ``inspectdb`` just can't detect certain scenarios and ask people to
edit their models manually.


Updatable primary keys in models
================================

The algorithm that determines what kind of database query to issue on
``model.save()`` is a fairly simple and well-documented one [6]_. If a 
row exists in the database with the value of its primary key equal to 
the saved object, it is updated, otherwise a new row is inserted. This
behavior is intuitive and works well for models where the primary key is
automatically created by the framework (be it an ``AutoField`` or a parent
link in the case of model inheritance).

However, as soon as the primary key is explicitly created, the behavior
becomes less intuitive and might be confusing, for example, to users of the
admin. For instance, say we have the following model::

    class Person(models.Model):
        first_name = models.CharField(max_length=47)
        last_name = models.CharField(max_length=47)
        shoe_size = models.PositiveSmallIntegerField()

        full_name = models.CompositeField(first_name, last_name,
                                          primary_key=True)

Then we register the model in the admin using the standard one-liner::

    admin.site.register(Person)

Since we haven't excluded any fields, all three fields will be editable in
the admin. Now, suppose there's an instance whose ``full_name`` is
``CompositeValue(first_name='Darth', last_name='Vadur')``. A user decides
to fix the last name using the admin, hits the “Save” button and instead
of fixing an existing record, a new one will appear with the new value,
while the old one remains untouched.  This behavior is clearly broken from
the point of view of the user.

It can be argued that it is the developer's fault that the database schema
is poorly chosen and that they expose the primary key to their users.
While this may be true in some cases, it is still to some extent a
subjective matter.

Therefore I propose a new behavior for ``model.save()`` where it would
detect a change in the instance's primary key and in that case issue an
``UPDATE`` for the right row, i.e. ``WHERE primary_key = previous_value``.

Of course, just going ahead and changing the behavior in this way for all
models would be backwards incompatible. To do this properly, we would need
to make this an opt-in feature. This can be achieved in multiple ways.

1) add a keyword argument such as ``update_pk`` to ``Model.save``
2) add a new option to ``Model.Meta``, ``updatable_pk``
3) make this a project-wide setting

Option 3 doesn't look pleasant and I think I can safely eliminate that.
Option 2 is somewhat better, although it adds a new ``Meta`` option.
Option 1 is the most flexible solution, however, it does not change the
behavior of the admin, at least not by default. This can be worked around
by overriding the ``save`` method to use a different default::

    class MyModel(models.Model):
        def save(self, update_pk=True, **kwargs):
            kwargs['update_pk'] = update_pk
            return super(MyModel, self).save(**kwargs)

To avoid the need to repeat this for each model, a class decorator might
be provided to perform this automatically.

In order to implement this new behavior a little bit of extra complexity
would have to be added to models. Model instances would need to store the
last known value of the primary key as retrieved from the database. On
save it would just find out whether the last known value is present and in
that case issue an ``UPDATE`` using the old value in the ``WHERE``
condition.

So far so good, this could be implemented fairly easily. However, the
problem becomes considerably more difficult as soon as we take into
account the fact that updating a primary key value may break foreign key
references. In order to avoid breaking references the ``on_delete``
mechanism of ``ForeignKey`` would have to be extended to support updates
as well. This means that the collector used by deletion will need to be
extended as well.

The problem becomes particularly nasty if we realize that a ``ForeignKey``
might be part of a primary key, which means the collector needs to keep
track of which field depends on which in a graph of potentially unlimited
size. Compared to this, deletion is simpler as it only needs to find a
list of all affected model instances as opposed to having to keep track of
which field to update using which value.

